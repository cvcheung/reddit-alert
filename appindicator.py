import os
import socket
import sys
from gi.repository import AppIndicator3
from gi.repository import Gtk
from gi.repository import Notify
from praw import objects as RObjects
from time import sleep
from webbrowser import open_new_tab


class RedditAlertAppIndicator:

    def __init__(self, fetch_method, refresh_time, expire_time, subreddits):
        if not Notify.init('RedditAlert'):
            sys.exit(1)
        self.delay = refresh_time
        self.fetch_method = fetch_method
        self.expiration = expire_time
        self.stored_subreddits = subreddits
        self.stored_subreddits.sort()
        self.uri = 'file://{0}/reddit.svg'.format(os.path.abspath(os.path.curdir))
        self.applet = AppIndicator3.Indicator.new_with_path('RedditAlertIndicator', 'reddit_applet',
                                                            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
                                                            '{}'.format(os.path.abspath(os.path.curdir)))
        self.applet.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.insert_location = 6

        # Initial dropdown menu for applet
        menu = Gtk.Menu()
        self.applet.set_menu(menu)

        # Add fetch method options
        self.fetch_group = []
        self.fetch_dict = {'Hot': RObjects.Subreddit.get_hot, 'New': RObjects.Subreddit.get_new,
                             'Rising': RObjects.Subreddit.get_rising, 'Top': RObjects.Subreddit.get_top,
                             'Controversial': RObjects.Subreddit.get_controversial}
        self.fetch = self.fetch_dict[fetch_method]
        fetch = Gtk.MenuItem(label='Change Fetch Method')
        fetch.show()
        menu.append(fetch)
        fetch_submenu = Gtk.Menu()
        for _ in ['Hot', 'New', 'Rising', 'Top', 'Controversial']:
            fetch_option = Gtk.RadioMenuItem.new_with_label(self.fetch_group, label=_)
            self.fetch_group = fetch_option.get_group()
            fetch_option.connect('activate', self.update_fetch)
            if _ == self.fetch:
                fetch_option.set_active(True)
            fetch_option.show()
            fetch_submenu.append(fetch_option)
        fetch.set_submenu(fetch_submenu)

        # Add refresh options
        self.refresh_group = []
        self.refresh_dict = {'30 seconds': 30, '60 seconds': 60, '2 minutes': 120, '3 minutes': 180,
                             '5 minutes': 300, '10 minutes': 600, '15 minutes': 900, '60 minutes': 3600}
        refresh = Gtk.MenuItem(label='Change Refresh Rate')
        refresh.show()
        menu.append(refresh)
        refresh_submenu = Gtk.Menu()
        for _ in ['30 seconds', '60 seconds', '2 minutes', '3 minutes', '5 minutes', '10 minutes',
                  '15 minutes', '60 minutes']:
            refresh_option = Gtk.RadioMenuItem.new_with_label(self.refresh_group, label=_)
            self.refresh_group = refresh_option.get_group()
            refresh_option.connect('activate', self.update_refresh)
            if self.delay == self.refresh_dict[_]:
                refresh_option.set_active(True)
            refresh_option.show()
            refresh_submenu.append(refresh_option)
        refresh.set_submenu(refresh_submenu)

        # Add notification expiration options
        self.expire_group = []
        self.expiration_dict = {'Default': Notify.EXPIRES_DEFAULT, 'Never': Notify.EXPIRES_NEVER}

        expire = Gtk.MenuItem(label='Change Notification Expiration')
        expire.show()
        menu.append(expire)
        expire_submenu = Gtk.Menu()
        for _ in ['Default', 'Never']:
            expire_option = Gtk.RadioMenuItem.new_with_label(self.expire_group, label=_)
            self.expire_group = expire_option.get_group()
            expire_option.connect('activate', self.update_expire)
            if self.expiration == self.expiration_dict[_]:
                expire_option.set_active(True)
            expire_option.show()
            expire_submenu.append(expire_option)
        expire.set_submenu(expire_submenu)

        # Add separator
        for _ in range(2):
            separator = Gtk.SeparatorMenuItem()
            separator.show()
            menu.append(separator)

        # Add save settings option
        save = Gtk.MenuItem(label='Save Settings')
        save.connect('activate', self.save_settings)
        save.show()
        menu.append(save)

        # Add separator
        separator = Gtk.SeparatorMenuItem()
        separator.show()
        menu.append(separator)

        # Add quit option
        quit_option = Gtk.MenuItem(label='Quit')
        quit_option.connect('activate', self.quit)
        quit_option.show()
        menu.append(quit_option)

        self.menu = menu

    @staticmethod
    def delay_call(function, *args):
        sleep(180)
        return function(*args)

    @staticmethod
    def network_test():
        try:
            host = socket.gethostbyname('reddit.com')
            socket.create_connection((host, 80), 2)
            return True
        except socket.error:
            pass
        return False

    @staticmethod
    def open(n, reddit_url, site_url):
        if reddit_url != site_url:
            open_new_tab(reddit_url)
        open_new_tab(site_url)
        n.close()
        Gtk.main_quit()

    @staticmethod
    def open_from_menu(menu_item, reddit_url):
        open_new_tab(reddit_url)

    @staticmethod
    def quit(menu_item):
        sys.exit(0)

    def invalid(self, subreddit):
        if subreddit in self.stored_subreddits:
            self.stored_subreddits.remove(subreddit)
        invalid_subreddit = Notify.Notification.new('Invalid subreddit', '/r/' + subreddit, self.uri)
        invalid_subreddit.show()

    def save_settings(self, menu_item):
        settings_file = open('.reddit-alert-settings', 'r+')
        settings_file.write('refresh = ' + str(self.fetch_method) + '\n')
        settings_file.write('refresh = ' + str(self.delay) + '\n')
        settings_file.write('expire = ' + str(self.expiration) + '\n')
        subreddits = ''
        self.stored_subreddits.sort()
        for _ in self.stored_subreddits:
            subreddits = subreddits + _ + ','
        settings_file.write('subreddits = ' + subreddits.rstrip(','))
        settings_file.close()
        Notify.Notification.new('Reddit Alert', 'Settings saved', self.uri).show()

    def update_expire(self, radio_item):
        if radio_item.get_active():
            self.expiration = self.expiration_dict[radio_item.get_label()]

    def update_fetch(self, radio_item):
        if radio_item.get_active():
            self.fetch_method = radio_item.get_label()
            self.fetch = self.fetch_dict[radio_item.get_label()]

    def update_refresh(self, radio_item):
        if radio_item.get_active():
            self.delay = self.refresh_dict[radio_item.get_label()]

if __name__ == '__main__':
    # Tests
    initial_settings_file = open('.reddit-alert-settings')
    try:
        method = initial_settings_file.readline().strip('\n').replace(' ', '').split('=')[1]
        delay = int(initial_settings_file.readline().strip('\n').replace(' ', '').split('=')[1])
        expiration = int(initial_settings_file.readline().strip('\n').replace(' ', '').split('=')[1])
        saved_subreddits = initial_settings_file.readline().strip('\n').replace(' ', '').split('=')[1].split(',')
    except IndexError:
        method = 'Hot'
        delay = 180
        expiration = -1
        saved_subreddits = []
    initial_settings_file.close()
    app = RedditAlertAppIndicator(method, delay, expiration, saved_subreddits)
    Gtk.main()
