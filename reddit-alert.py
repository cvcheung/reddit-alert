#!/usr/bin/env python

import praw
from appindicator import RedditAlertAppIndicator
from gi.repository import Notify
from gi.repository import Gtk
from gi.repository import GLib
from itertools import chain
from Queue import Queue
from subredditwindow import SubredditWindow


SUBREDDIT_MENU_ITEMS = 10


class RedditAlert(RedditAlertAppIndicator):

    def __init__(self, refresh_time, expire_time, subreddits):
        RedditAlertAppIndicator.__init__(self, refresh_time, expire_time, subreddits)
        self.agent = praw.Reddit('reddit-alert')
        self.subreddits = []
        self.visited = []
        self.subreddit_drawer = {}
        self.subreddit_menu_item = {}
        self.active = False
        change_subreddits = Gtk.MenuItem(label='Add/Delete Subreddit(s)')
        change_subreddits.connect('activate', self.subreddit_manager)
        change_subreddits.show()
        self.menu.prepend(change_subreddits)
        refresh_now = Gtk.MenuItem(label='Refresh Now')
        refresh_now.connect('activate', self.refresh_now)
        refresh_now.show()
        self.menu.insert(refresh_now, 3)
        self.add_subreddits(*self.stored_subreddits)

    def add_subreddits(self, *subreddits):
        if not self.network_test():
            self.delay_call(self.add_subreddits, subreddits)
        for _ in subreddits:
            try:
                subreddit = self.agent.get_subreddit(_, fetch=True)
            except praw.errors.InvalidSubreddit:
                self.invalid(_)
                return False
            except praw.errors.NotFound:
                self.invalid(_)
                return False
            id = _.lower()
            if id not in self.stored_subreddits:
                self.stored_subreddits.append(id)
            if subreddit not in self.subreddits:
                self.subreddits.append(subreddit)
                self.add_subreddit_menu_item(id, subreddit.display_name)
        return True

    def add_subreddit_menu_item(self, subreddit, title):
        subreddit_menu = Gtk.MenuItem(label=title)
        subreddit_menu.show()
        subreddit_menu_drawer = Gtk.Menu()
        subreddit_menu.set_submenu(subreddit_menu_drawer)
        self.stored_subreddits.sort()
        self.menu.insert(subreddit_menu, self.insert_location + self.stored_subreddits.index(subreddit))
        self.subreddit_drawer[subreddit] = subreddit_menu_drawer, Queue(SUBREDDIT_MENU_ITEMS)
        self.subreddit_menu_item[subreddit] = subreddit_menu

    def main(self):
        self.monitor()
        GLib.timeout_add_seconds(self.delay, self.monitor)
        Gtk.main()

    def monitor(self):
        for submission in self.refresh():
            if submission.id not in self.visited:
                self.visited.append(submission.id)
                title, text = submission.title, '/r/' + submission.subreddit.display_name
                link = submission.url
                reddit_link = submission.permalink
                alert = Notify.Notification.new(title, text, self.uri)
                if 'self' in submission.domain:
                    alert.add_action(reddit_link, 'Link', self.open, reddit_link)
                else:
                    alert.add_action(reddit_link, 'Link', self.open, link)
                alert.connect('closed', Gtk.main_quit)
                alert.show()
                Gtk.main()
                link_menu_item = Gtk.MenuItem(label=title)
                link_menu_item.connect('activate', self.open_from_menu, reddit_link)
                link_menu_item.show()
                main_menu, q = self.subreddit_drawer[submission.subreddit.display_name.lower()]
                if q.full():
                    main_menu.remove(q.get())
                q.put(link_menu_item)
                main_menu.append(link_menu_item)

    def refresh(self):
        if not self.network_test():
            self.delay_call(self.refresh)
        return chain(*map(praw.objects.Subreddit.get_new, self.subreddits))

    def refresh_now(self, menu_item):
        self.monitor()

    def remove_subreddit(self, subreddit):
        name = subreddit.lower()
        if name not in self.stored_subreddits:
            return False
        self.stored_subreddits.remove(name)
        menu, q = self.subreddit_drawer.pop(name)
        menu.deactivate()
        self.menu.remove(self.subreddit_menu_item.pop(name))
        for _ in self.subreddits:
            if name == _.display_name.lower():
                self.subreddits.remove(_)
                return True

    def subreddit_manager(self, menu_item):
        if self.active:
            return
        self.active = True
        SubredditWindow(self)
        self.active = False

if __name__ == '__main__':
    # Import settings
    initial_settings_file = open('.reddit-alert-settings')
    try:
        delay = int(initial_settings_file.readline().strip('\n').replace(' ', '').split('=')[1])
        expiration = int(initial_settings_file.readline().strip('\n').replace(' ', '').split('=')[1])
        saved_subreddits = initial_settings_file.readline().strip('\n').replace(' ', '').split('=')[1].split(',')
    except IndexError:
        delay = 180
        expiration = -1
        saved_subreddits = []
    initial_settings_file.close()

    # Create applet
    alertme = RedditAlert(delay, expiration, saved_subreddits)

    # Run applet
    alertme.main()
