import os
from gi.repository import Gtk
from gi.repository import Notify


class SubredditWindow(Gtk.Window):

    def __init__(self, app_instance):
        Gtk.Window.__init__(self, title='Add/Delete Subreddit(s)')
        self.app_instance = app_instance

        # Main Window Box
        self.set_resizable(False)
        self.set_default_icon_from_file('{0}/reddit_applet.svg'.format(os.path.abspath(os.path.curdir)))
        self.set_size_request(400, 10)
        self.set_border_width(10)
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(main_box)

        # Box with entry and buttons
        entry_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        main_box.pack_start(entry_box, True, True, 0)

        self.entry = Gtk.Entry()
        entry_box.pack_start(self.entry, True, True, 0)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_box.pack_start(button_box, True, True, 0)

        for name, action in [('Add', self.add_subreddit), ('Delete', self.delete_subreddit)]:
            button = Gtk.Button(label=name)
            button.set_size_request(1, 1)
            button.connect('clicked', action)
            button_box.pack_start(button, True, True, 0)

        self.main()

    def add_subreddit(self, button):
        result = self.app_instance.add_subreddits(self.entry.get_text())
        if result:
            Notify.Notification.new('Reddit Alert', 'Subreddit added', self.app_instance.uri).show()

    def delete_subreddit(self, button):
        result = self.app_instance.remove_subreddit(self.entry.get_text())
        if result:
            Notify.Notification.new('Reddit Alert', 'Subreddit deleted', self.app_instance.uri).show()

    def main(self):
        Notify.init('SubredditsManager')
        self.connect("delete-event", Gtk.main_quit)
        self.show_all()
        Gtk.main()
