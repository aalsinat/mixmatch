import json
import logging
import os
import sys

import wx

from mixmatch.actions import Action
from mixmatch.conf import BASE_DIR
from .api import RestClient, Coupon

# Constants for returning status on view showing coupon list
VIEW_REDEEM = 'REDEEM'
VIEW_CANCEL = 'CANCEL'
VIEW_EXIT = 'EXIT'


class ICoupon(Action):
    def __init__(self, constructor=()):
        super(ICoupon, self).__init__(constructor)
        self.current_coupons_list = self._retrieve_stored_info()

    def show_coupons(self, barcode, icg_extend):
        self.logger.info('Showing coupons list')
        coupons_list = self._get_coupons(barcode)
        coupons_list = self._get_mocking_coupons()

        if len(coupons_list) > 0:
            self.logger.info('Coupons list length is %d', len(coupons_list))
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
                selected_list = self._merge_coupon_lists(view.coupons, self.current_coupons_list)
                if len(selected_list) > 0:
                    self.logger.info('New selected list: %s', selected_list)
                    icg_extend.save_coupon(selected_list)
                    # 3. Update database
                    value = sum(coupon.value for coupon in selected_list)
                    self.logger.info('New value for coupons list %s', value)
                    icg_extend.update_db_promotion(value)
                else:
                    icg_extend.cancel_mix_and_match()
                    icg_extend.update_db_promotion(0.0)
                    icg_extend.cancel_coupon()
                    icg_extend.set_mix_and_match_status('No coupons selected for redemption.')
            elif view.action == VIEW_CANCEL:
                icg_extend.cancel_mix_and_match()
                icg_extend.update_db_promotion(0.0)
                icg_extend.cancel_coupon()
                icg_extend.set_mix_and_match_status('Cancelled redemption.')
            else:
                self.logger.info('Nothing has been done')
            self.logger.info('Returned list from Screen: %s', view.coupons)
        else:
            icg_extend.set_mix_and_match_status('There are no coupons up to date to be redeemed.')

    @staticmethod
    def _mark_as_selected(selected_list, coupon):
        if coupon in selected_list:
            coupon.selected = True
        return coupon

    @staticmethod
    def _merge_coupon_lists(final_list, stored_list):
        current_list = stored_list[:]
        for coupon in final_list:
            if coupon in stored_list and not coupon.selected:
                current_list.remove(coupon)
            elif coupon not in stored_list and coupon.selected:
                current_list.append(coupon)
        return current_list

    def _get_client(self):
        return RestClient({
            'grant_type': self.properties.get('token.grant_type'),
            'client_id': self.properties.get('token.client_id'),
            'client_secret': self.properties.get('token.client_secret'),
            'base_url': self.properties.get('ws.base.url'),
            'login_url': self.properties.get('ws.token.url'),
            'coupons_url': self.properties.get('ws.coupons.list.url'),
            'location': self.properties.get('location.ref'),
            'service_provider': self.properties.get('service.provider.ref'),
            'trading_outlet': self.properties.get('trading.outlet.ref')
        })

    def _retrieve_stored_info(self):
        saved_coupons_file = os.path.abspath(
            os.path.join(BASE_DIR, self.properties.get('store.path'), self.properties.get('store.filename')))
        if os.path.isfile(saved_coupons_file):
            with open(saved_coupons_file) as saved_coupons:
                return map(lambda c: Coupon(c), json.load(saved_coupons))
        else:
            return []

    def _get_coupons(self, barcode):
        valid_coupons = []
        try:
            selected_coupons = self._retrieve_stored_info()
            status, requested_coupons = self._get_client().get_coupons(barcode)
            if status == 200:
                actual_coupons = map(lambda coupon: self._mark_as_selected(selected_coupons, coupon), requested_coupons)
                valid_coupons = filter(lambda coupon: not coupon['redeemed'] and not coupon['expired'], actual_coupons)
        except Exception as e:
            self.logger.info('An exception has occurred %s', e.message)
        finally:
            return valid_coupons

    def _get_mocking_coupons(self):
        saved_coupons_file = os.path.abspath(
            os.path.join(BASE_DIR, './mixmatch/actions/icoupon/mocking', 'icoupon_response.json'))
        if os.path.isfile(saved_coupons_file):
            with open(saved_coupons_file) as saved_coupons:
                return map(lambda c: Coupon(c), json.load(saved_coupons))
        else:
            return []


class CouponsView(wx.Frame):
    def __init__(self, parent, coupons, icg_extend):
        self.logger = logging.getLogger(self.__class__.__name__)
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
                                      wx.Bitmap(CouponsView.resource_path(u'img/icoupon.png'), wx.BITMAP_TYPE_ANY),
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
            if not coupon['redeemed'] and not coupon['expired']:
                btn = wx.ToggleButton(button_list_scrolled_window, wx.ID_ANY, coupon['couponTypeName'],
                                      wx.DefaultPosition,
                                      wx.Size(-1, 150), wx.BORDER_DEFAULT, name=coupon['couponRef'], )
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
        Selecting a coupon involves updating the list of coupons to redeem. Depending on the status of the toggle button, we will add or remove the reference to that coupon.
        """
        btn = event.GetEventObject()
        if btn.GetValue():
            btn.SetBackgroundColour(wx.Colour(128, 255, 128))
        else:
            btn.SetBackgroundColour(wx.Colour(255, 255, 255))
        for coupon in self.coupons:
            if coupon.couponRef == btn.GetName():
                coupon.selected = btn.GetValue()
                self.logger.info('Change value for button %s to %s', btn.GetName(), btn.GetValue())

    def redeem(self, event):
        """
        Redeeming a coupon involves modifying the value of the discount in the database. We will save the coupon reference in a file for further post-ticket processing.
        :param event: The event of clicking the coupon button to apply.
        :return:
        """
        self.action = VIEW_REDEEM

        self.logger.info('Leaving coupons list view with %s', self.action)
        self.Close()

    def cancel(self, event):
        """
        Cancelling redemption involves modifying ICG exchange file update and deleting any coupon reference file for further post-ticket processing.
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
            return os.path.join(sys._MEIPASS, relative_path)
        temp = os.path.join(os.path.abspath("."), relative_path)
        print 'Relative path: %s' % relative_path
        print 'Resource path for wxPython: %s' % temp
        return temp
        #return os.path.join(os.path.abspath("."), relative_path)

    def __del__(self):
        pass
