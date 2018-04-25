import sys
from json import loads
from logging import getLogger
from os import path

import wx

from mixmatch.actions import IApplicable, PatternMatcher
from mixmatch.conf import BASE_DIR
from .api import RestClient, Coupon
from .exceptions import AuthenticationError, VoucherAvailabilityRequestError

# Constants for returning status on view showing coupon list
VIEW_REDEEM = 'REDEEM'
VIEW_CANCEL = 'CANCEL'
VIEW_EXIT = 'EXIT'


class Action(IApplicable):
    ACTION_NAME = 'IBERIA'
    voucher_pattern = r'^(cvou:)?((0002\d{2})(\d{7}))(e)?$'
    ticket_pattern = r'^\d{13}$'

    def __init__(self, iterable=(), **properties):
        super(Action, self).__init__(iterable, **properties)

    def get_name(self):
        return type(self).ACTION_NAME

    def __get_client(self):
        return RestClient({
            'base_url': self['ws.base.url.prod'],
            'user': self['ws.user'],
            'password': self['ws.pwd'],
            'airport': self['voucher.airport'],
            'id_provider': self['voucher.id_provider']
        })

    def __get_coupons(self, barcode):
        status, coupons_list = self.__get_client().get_coupons(barcode)
        return coupons_list

    def __retrieve_stored_info(self):
        saved_coupons_file = path.abspath(
            path.join(BASE_DIR, self['store.path'], self['store.filename']))
        if path.isfile(saved_coupons_file):
            file = open(saved_coupons_file, 'r')
            saved_coupons = file.read()
            file.close()
            return list(map(lambda c: Coupon(identifier=c.id, name=c.name, is_redeemable=c.is_redeemable),
                            loads(saved_coupons)))
        else:
            return []

    def __is_voucher(self, barcode):
        return self.__get_client().is_voucher(barcode)

    def check_pattern(self, barcode: str, matcher: PatternMatcher) -> str:
        return matcher.match(barcode, 4, 6)

    def apply(self, icg_extend):
        """
        Si el codigo que escaneamos en un billete o un boarding pass, debemos mostrar la lista de vouchers
        que nos devuelve el servicio.
        En el caso de los bonos, la respuesta solo nos va a devolver una gratuidad, de modo que no debemos mostrar
        nada.
        :param icg_extend:
        :return:
        """
        match = self.check_pattern(icg_extend.get_barcode(), PatternMatcher(self['mixmatch.pattern']))
        if match is not None:
            is_voucher = True if match[0] is not None else False
            try:
                coupons_list = self.__get_coupons(icg_extend.get_barcode())
                self.logger.info('List of coupons:\n %s', coupons_list)
                # Given a coupons list we should show them using a windows form:
                # Options:
                #   - List of buttons on the header
                #   - Path to logo to be displayed
                #   - List of coupons to be shown. Given a list of objects, we should transform them

                if len(coupons_list) > 0:
                    self.logger.debug('Coupons list length is %d', len(coupons_list))
                    if not self.__is_voucher(icg_extend.get_barcode()):
                        app = wx.App()
                        view = CouponsView(None, coupons_list, icg_extend)
                        view.ShowFullScreen(True)
                        # view.Maximize(True)
                        app.MainLoop()
                        if view.action == VIEW_REDEEM:
                            # 1. Exchange file update, changing aplicarmm tag value with manager.promotion.id value
                            icg_extend.set_mix_and_match()
                            icg_extend.set_mix_and_match_status('Coupons selected successfully')
                            # 2. Create a new file for saving selected coupons merged with previous stored ones.
                            selected_list = list(filter(lambda c: c.selected, view.coupons))
                            if len(selected_list) > 0:
                                self.logger.debug('New selected list: %s', selected_list)
                                icg_extend.save_coupon(self.get_name(), selected_list)
                            else:
                                icg_extend.cancel_mix_and_match()
                                icg_extend.cancel_coupon()
                                icg_extend.set_mix_and_match_status('No coupons selected for redemption.')
                        elif view.action == VIEW_CANCEL:
                            icg_extend.cancel_mix_and_match()
                            icg_extend.cancel_coupon()
                            icg_extend.set_mix_and_match_status('Cancelled redemption.')
                        else:
                            self.logger.debug('Nothing has been done')
                            icg_extend.cancel_coupon()
                        self.logger.debug('Returned list from Screen: %s', view.coupons)
                    else:
                        # When the scanned value corresponds to a voucher, the value returned will be only one.
                        icg_extend.set_mix_and_match()
                        icg_extend.set_mix_and_match_status('Coupons selected successfully')
                        icg_extend.save_coupon(self.get_name(), coupons_list)

                else:
                    icg_extend.set_mix_and_match_status('There are no coupons up to date to be redeemed.')
            except AuthenticationError as auth:
                self.logger.error(auth.message)
            except VoucherAvailabilityRequestError as e:
                self.logger.error(e.message)
            except Exception as e:
                self.logger.error(str(e))
        else:
            self.logger.debug('Scanned value does not match %s pattern.', self.get_name())


# TODO: En el constructor debemos incorporar un parametro para decidir si se puede seleccionar uno o multiples cupones

class CouponsView(wx.Frame):
    def __init__(self, parent, coupons, icg_extend):
        self.logger = getLogger(self.__class__.__name__)
        self.coupons = coupons
        self.action = VIEW_EXIT
        self.extend = icg_extend
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u'Coupons List', pos=wx.DefaultPosition,
                          size=wx.Size(600, 400), style=wx.STAY_ON_TOP)
        self.init_ui()
        self.SetFocus()
        # self.Show()
        # self.Maximize(True)
        # self.make_modal()

    def init_ui(self):
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        # ********************************
        # Vertical layout: header / body
        # ********************************
        vertical_layout_box_sizer = wx.BoxSizer(wx.VERTICAL)
        # ---------------
        # Header section
        # ---------------
        header_panel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(-1, 40), wx.TAB_TRAVERSAL)
        header_panel.SetBackgroundColour(wx.Colour(188, 31, 82))
        header_panel.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        # Header layout
        header_layout_grid_sizer = wx.GridSizer(1, 2, 0, 0)
        header_layout_grid_sizer.SetMinSize(wx.Size(-1, 40))
        # Title section
        title = wx.StaticText(header_panel, wx.ID_ANY, u"Escoja cupones de la lista:", wx.DefaultPosition,
                              wx.DefaultSize, 0)
        title.Wrap(-1)
        title.SetFont(
            wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD,
                    False, wx.EmptyString))
        header_layout_grid_sizer.Add(title, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER, 5)
        # Action button section
        action_button_box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # Redeem button
        redeem_button = wx.Button(header_panel, wx.ID_ANY, u'Redimir cupones', wx.DefaultPosition, wx.DefaultSize, 0)
        redeem_button.Bind(wx.EVT_BUTTON, self.redeem)
        redeem_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        action_button_box_sizer.Add(redeem_button, 0, wx.ALIGN_RIGHT | wx.SHAPED | wx.EXPAND, 1)
        # Cancel button
        # cancel_button = wx.Button(header_panel, wx.ID_ANY, u'Cancel redeem', wx.DefaultPosition, wx.DefaultSize, 0)
        # cancel_button.Bind(wx.EVT_BUTTON, self.cancel)
        # cancel_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        # action_button_box_sizer.Add(cancel_button, 0, wx.ALIGN_RIGHT | wx.SHAPED | wx.EXPAND, 1)
        # Exit button
        exit_button = wx.Button(header_panel, wx.ID_ANY, u'Salir', wx.DefaultPosition, wx.DefaultSize, 0)
        exit_button.Bind(wx.EVT_BUTTON, self.exit)
        exit_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        action_button_box_sizer.Add(exit_button, 0, wx.ALIGN_RIGHT | wx.SHAPED | wx.EXPAND, 1)

        header_layout_grid_sizer.Add(action_button_box_sizer, 0, wx.ALIGN_RIGHT | wx.SHAPED | wx.EXPAND, 1)
        header_panel.SetSizer(header_layout_grid_sizer)
        header_panel.Layout()

        vertical_layout_box_sizer.Add(header_panel, 0, wx.EXPAND, 5)

        # ---------------
        # Body section
        # ---------------
        body_panel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(-1, 40), wx.TAB_TRAVERSAL)
        body_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        # ********************************
        # Body layout: logo / coupons list
        # ********************************
        body_layout_box_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # iCoupon logo section
        logo_panel = wx.Panel(body_panel, wx.ID_ANY, wx.DefaultPosition, wx.Size(1, 1), wx.TAB_TRAVERSAL)
        logo_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        logo_grid_sizer = wx.GridSizer(0, 0, 0, 0)
        logo_bitmap = wx.StaticBitmap(logo_panel, wx.ID_ANY,
                                      wx.Bitmap(CouponsView.resource_path(u'mixmatch/actions/iberia/img/logo.png'),
                                                wx.BITMAP_TYPE_ANY),
                                      wx.DefaultPosition, wx.DefaultSize, 0)
        logo_bitmap.SetBackgroundColour(wx.Colour(255, 255, 255))
        logo_grid_sizer.Add(logo_bitmap, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 1)

        logo_panel.SetSizer(logo_grid_sizer)
        logo_panel.Layout()

        body_layout_box_sizer.Add(logo_panel, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 1)

        # Button list section
        button_list_scrolled_window = wx.ScrolledWindow(body_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                                        wx.VSCROLL)
        button_list_scrolled_window.SetScrollRate(5, 5)
        button_list_scrolled_window.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_APPWORKSPACE))
        button_list_scrolled_window.EnableScrolling(False, True)

        buttons_grid_sizer = wx.GridSizer(len(self.coupons), 1, 0, 0)
        buttons_grid_sizer = wx.BoxSizer(wx.VERTICAL)

        for coupon in self.coupons:
            if coupon.is_redeemable:
                btn = wx.ToggleButton(button_list_scrolled_window, wx.ID_ANY, coupon.name,
                                      wx.DefaultPosition,
                                      wx.Size(-1, 150), wx.BORDER_DEFAULT, name=str(coupon.id), )
                btn.SetValue(coupon.selected)
                if btn.GetValue():
                    btn.SetBackgroundColour(wx.Colour(128, 255, 128))
                else:
                    btn.SetBackgroundColour(wx.Colour(255, 255, 255))
                btn.Bind(wx.EVT_TOGGLEBUTTON, self.select_coupon)
                buttons_grid_sizer.Add(btn, 0, wx.EXPAND, 5)

        button_list_scrolled_window.SetSizer(buttons_grid_sizer)
        button_list_scrolled_window.Layout()
        buttons_grid_sizer.Fit(button_list_scrolled_window)

        body_layout_box_sizer.Add(button_list_scrolled_window, 1, wx.EXPAND | wx.ALL, 1)

        body_panel.SetSizer(body_layout_box_sizer)
        body_panel.Layout()
        body_layout_box_sizer.Fit(body_panel)

        vertical_layout_box_sizer.Add(body_panel, 1, wx.EXPAND | wx.ALL, 1)

        self.SetSizer(vertical_layout_box_sizer)
        self.Layout()

        self.Centre(wx.BOTH)

    def select_coupon(self, event):
        """
        Selecting a coupon involves updating the list of coupons to redeem. Depending on the status of the toggle
        button, we will add or remove the reference to that coupon.
        """
        clicked_button = event.GetEventObject()
        buttons_list = clicked_button.Parent.Children
        for coupon in self.coupons:
            coupon.selected = clicked_button.GetValue() if str(coupon.id) == clicked_button.GetName() else False
        # Changes button background color and value depending on its selection status
        for button in buttons_list:
            if clicked_button.GetName() == button.GetName():
                button.SetBackgroundColour(wx.Colour(128, 255, 128))
                button.SetValue(True)
            else:
                button.SetBackgroundColour(wx.Colour(255, 255, 255))
                button.SetValue(False)

    def redeem(self, event):
        """
        Redeeming a coupon involves modifying the value of the discount in the database. We will save the coupon
        reference in a file for further post-ticket processing. :param event: The event of clicking the coupon button
        to apply. :return:
        """
        self.action = VIEW_REDEEM

        self.logger.info('Leaving coupons list view with %s', self.action)
        self.Close()

    def cancel(self, event):
        """
        Cancelling redemption involves modifying ICG exchange file update and deleting any coupon reference file for
        further post-ticket processing.
        """
        self.action = VIEW_CANCEL
        self.logger.info('Leaving coupons list view with %s', self.action)
        self.Close()

    def exit(self, event):
        """
        Exiting coupons list redemption screen without doing anything.
        """
        self.action = VIEW_EXIT
        self.logger.info('Leaving coupons list view with %s', self.action)
        self.Close()

    @staticmethod
    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        if hasattr(sys, '_MEIPASS'):
            return path.join(sys._MEIPASS, relative_path)
        temp = path.join(path.abspath("."), relative_path)
        print('Relative path: %s' % relative_path)
        print('Resource path for wxPython: %s' % temp)
        return temp
        # return path.join(path.abspath("."), relative_path)

    def __del__(self):
        pass
