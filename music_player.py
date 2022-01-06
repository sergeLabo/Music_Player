
from time import sleep
import datetime
import subprocess
from threading import Thread
from functools import partial
from pathlib import Path
import platform

import kivy
kivy.require('2.0.0')

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty, NumericProperty

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image

from kivy.core.image import Image as CoreImage
from kivy.core.window import Window

from just_playback import Playback

from library import get_lib_infos, get_tracks, dict_to_OrderdDict


Window.size = (800, 480)
if 'arm'  in platform.machine():
    Window.fullscreen = True


class LoadDialog(FloatLayout):
    """Shows the load dialog box, that contains file browser"""

    load = ObjectProperty(None)  # initiates self.library_change()
    cancel = ObjectProperty(None)  # initiates self.dismiss_popup()


class MainScreen(Screen):
    """Ecran principal, l'appli s'ouvre sur cet écran
    root est le parent de cette classe dans la section <MainScreen> du kv
    """
    pause_play_text = StringProperty("")
    fichier = ObjectProperty(None)
    library = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.app = App.get_running_app()
        self.library = self.app.config.get('library', 'path')
        self.current_dir = str(Path(__file__).parent.absolute())
        print("Dossier courrant:", self.current_dir)
        self.lib_infos = get_lib_infos(self.library, self.current_dir)

    def on_touch_move(self, touch):
        if touch.dx < -10:
            self.app.screen_manager.transition.direction = 'left'
            self.app.screen_manager.current = 'Albums'

    def dismiss_popup(self):
        """Removes pop up box"""
        self.popup.dismiss()

    def show_load(self):
        """Creates a pop-up instance, using contents of the Dialog box,
        and opens it
        """
        # passes load and cancel function to LoadDialog
        content = LoadDialog(load=self.library_change, cancel=self.dismiss_popup)
        self.popup = Popup(title="Sélection de la Bibliothèque",
                           content=content,
                           size_hint=(0.9, 0.9))
        self.popup.open()

    def library_change(self, filechooser_path):
        """Changement de chemin pour la bibliothèque"""
        # closes show_load pop-up once dir is selected
        self.dismiss_popup()
        # Actialisation
        self.library = filechooser_path
        # Sauvegarde dans .ini
        self.app.config.set('library', 'path', self.library)
        self.app.config.write()
        print(f"Library {self.library} saved in config")

    def quit(self):
        scr = self.app.screen_manager.get_screen('Player')
        scr.loop = 0
        self.app.do_quit()

    def shutdown(self):
        subprocess.run(['sudo', 'shutdown', 'now'])


class Albums(Screen):

    def __init__(self, **kwargs):
        """Les albums sont les clé de lib_infos
        l = {'nom du dossier parent': { 'album': 'toto',
                                        'artist':,
                                        'cover':,
                                        'titres': { 0: ('tata', 'chemin abs'),
                                                    1: ('titi', 'chemin abs')}}}
        """
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        scr = self.app.screen_manager.get_screen('Main')
        self.lib_infos = scr.lib_infos
        self.album_current = None
        Clock.schedule_once(self.add_cover_buttons, 1)

    def on_touch_move(self, touch):
        if touch.dx > 10:
            self.app.screen_manager.transition.direction = 'right'
            self.app.screen_manager.current = 'Main'
        if touch.dx < -10:
            self.app.screen_manager.transition.direction = 'left'
            self.app.screen_manager.current = 'Player'

    def add_cover_buttons(self, dt):

        self.size = (Window.width, Window.height)
        layout = GridLayout(cols=3,
                            spacing=(10, 10),
                            padding=(10, 10))
        layout.size_hint_y= None
        # Make sure the height is such that there is something to scroll.
        layout.bind(minimum_height=layout.setter('height'))

        for key in self.lib_infos.keys():
            # key = 'nom du dossier parent'
            album = key
            cover = self.lib_infos[key]['cover']
            button = Button(background_normal=cover,
                            background_down='covers/default_cover.png',
                            size_hint_y=None,
                            height=int((self.size[0]-40)/3))
            buttoncallback = partial(self.set_selected_album, album)
            button.bind(on_release=buttoncallback)
            layout.add_widget(button)

        self.ids.album_scroll.add_widget(layout)

    def set_selected_album(self, album, instance):

        # Définition du nouvel album
        self.album_current = album

        # Lancement du player
        scr = self.app.screen_manager.get_screen('Player')
        scr.piste = 1
        scr.player_main()
        # Lancement des Tacks
        scr = self.app.screen_manager.get_screen('Tracks')
        scr.add_tracks()

        # Bascule sur écran Player
        self.app.screen_manager.current = 'Player'


class Player(Screen):
    maxi = NumericProperty(100)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.playback = None
        self.piste = 1
        self.loop = 1

    def on_touch_move(self, touch):
        if touch.dx > 10:
            self.app.screen_manager.transition.direction = 'right'
            self.app.screen_manager.current = 'Albums'
        if touch.dx < -10:
            self.app.screen_manager.transition.direction = 'left'
            self.app.screen_manager.current = 'Tracks'

    def player_main(self):
        """
        l = {'nom du dossier parent': { 'album': 'toto',
                                        'artist': '',
                                        'cover': '',
                                        'titres': { 0: ('tata', 'chemin abs'),
                                                    1: ('titi', 'chemin abs')}}}

        tracks = OrderedDict([
        (1, ('Bonheur', '/media/data/3D/music/flacs/Vieux_Farka_Touré_Samba/Vieux Farka Touré - Samba - 01 Bonheur.flac')),
        (2, ('Mariam (feat. Idan Raichel)', '/media/data/3D/music/flacs/Vieux_Farka_Touré_Samba/Vieux Farka Touré - Samba - 02 Mariam (feat. Idan Raichel).flac')), ...
        """
        scr = self.app.screen_manager.get_screen('Albums')
        self.lib_infos = scr.lib_infos

        # clé du dict self.lib_infos = 'nom du dossier parent'
        self.album = scr.album_current

        tracks = get_tracks(self.lib_infos, self.album)
        self.keys = list(tracks.keys())
        self.play_track()
        self.loop = 1

    def play_track(self):
        """Je joue bidule: le fichier de la piste
        loops_at_end
        """
        self.bibule = self.lib_infos[self.album]['titres'][self.piste][1]
        self.title = self.lib_infos[self.album]['titres'][self.piste][0]
        self.album_name = self.lib_infos[self.album]['album']
        self.artist = self.lib_infos[self.album]['artist']
        self.cover = self.lib_infos[self.album]['cover']
        self.maxi = self.lib_infos[self.album]['titres'][self.piste][2]
        print(f"\nPlay de:\n    {self.piste}: {self.title}\n\n")

        if self.playback:
            self.playback.stop()
        self.playback = Playback()
        self.playback.load_file(self.bibule)
        self.playback.play()
        self.loop = 1
        self.thread_to_get_end()

        self.ids.track_number.text = str(self.piste)
        self.ids.play_pause.disabled = False
        # make slider appear when song is loaded
        self.ids.song_slider.opacity = 1
        self.ids.song_slider.disabled = False

        self.music_information()
        self.ids.play_pause.background_normal = "images/Pause-normal.png"

    def thread_to_get_end(self):
        Thread(target=self.get_end).start()

    def get_end(self):
        while self.loop:
            if not self.playback.active:
                self.loop = 0
                self.playback.stop()
                if self.piste < len(self.keys):
                    self.piste += 1
                    self.play_track()
                else:
                    self.app.screen_manager.current = ("Albums")
                    self.piste = 1
                    Clock.unschedule(self.event_info)
                    sleep(0.5)
                    self.playback = None
            sleep(1)

    def new_track(self, track):
        """From sceen Tracks"""
        self.loop = 0
        self.playback.stop()
        self.piste = track
        self.play_track()

    def play_pause(self):
        """Toggles between play/resume and pause functions"""
        if self.ids.play_pause.background_normal == "images/Pause-normal.png":
            self.playback.pause()
            self.ids.play_pause.background_normal = "images/Play-normal.png"
            self.ids.play_pause.background_down = "images/Play-down.png"
            # Pour palier à la latence le la pi
            sleep(0.1)
        elif self.ids.play_pause.background_normal == "images/Play-normal.png":
            self.playback.resume()
            self.ids.play_pause.background_normal = "images/Pause-normal.png"
            self.ids.play_pause.background_down = "images/Pause-down.png"
            # Pour palier à la latence le la pi
            sleep(0.1)

    def song_position(self, dt):
        """Displays duration of song in hh:mm:ss, and updates slider"""
        if self.playback:
            # current song position
            current_pos = datetime.timedelta(seconds=self.playback.curr_pos)
            current_pos = str(current_pos)[:7]

            # total duration of song
            track_length = datetime.timedelta(seconds=self.playback.duration)
            track_length = str(track_length)[:7]

            # updates text
            self.ids.current_position.text = f"{current_pos} | {track_length}"
            # updates slider position
            self.ids.song_slider.value = int(self.playback.curr_pos)

    def change_position(self, value):
        """Syncs position of song with slider position"""
        try:
            self.playback.seek(int(value))
        except:
            pass

    def music_information(self):
        """Displays song duration, title, album and artist"""

        unknown = ["Unknown Title", "Unknown Album", "Unknown Artist"]

        # Calls on clock module to repeatedly update audio slider
        if self.playback.active:
            self.ids.song_slider.max = int(self.playback.duration)
            self.event_info = Clock.schedule_interval(self.song_position, 1)

            self.ids.title.text = self.title
            self.ids.album.text = self.album_name
            self.ids.artist.text = self.artist
            self.ids.album_art.source = self.cover

        # Create an animated title that scrolls horizontally
        scrolling_effect = Animation(x=0, duration=1)  # opacity=0,
        scrolling_effect += Animation(x=800, duration=40)  #  opacity=1,
        scrolling_effect.repeat = True
        scrolling_effect.start(self.ids.title)


class Tracks(Screen):
    # Attribut de class, obligatoire pour appeler root.titre dans kv
    titre = StringProperty("toto")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.layout = None

    def on_touch_move(self, touch):
        if touch.dx > 10:
            self.app.screen_manager.transition.direction = 'right'
            self.app.screen_manager.current = 'Player'

    def add_tracks(self):
        """
        l = {'nom du dossier parent': { 'album': 'toto',
                                        'artist':,
                                        'cover':,
                                        'titres': { 0: ('tata', 'chemin abs'),
                                                    1: ('titi', 'chemin abs')}}}
        """
        self.size = (Window.width, Window.height)

        # Remove widgets of previous album
        if self.layout:
            self.ids.tracks_scroll.remove_widget(self.layout)

        self.layout = GridLayout(cols=1,
                            spacing=(20, 20),
                            padding=(10, 10))
        self.layout.size_hint_y= None
        # Make sure the height is such that there is something to scroll.
        self.layout.bind(minimum_height=self.layout.setter('height'))

        # Le OrderedDict est perdu par l'appel dans les autres classes
        scr = self.app.screen_manager.get_screen('Albums')
        dico = dict_to_OrderdDict(scr.lib_infos[scr.album_current]['titres'])
        for key, val in dico.items():
            text = (f"Piste N° {key}\n"
                    f"{val[0]}")
            button = Button(size_hint_y=None,
                            background_color=(2.8, 2.8, 2.8, 1),
                            color=(0, 0, 0, 1),
                            font_size=32,
                            text=text)
            buttoncallback = partial(self.set_selected_track, key)
            button.bind(on_press=buttoncallback)
            self.layout.add_widget(button)

        self.ids.tracks_scroll.add_widget(self.layout)

    def set_selected_track(self, track, instance):
        self.current_track = track
        scr = self.app.screen_manager.get_screen('Player')
        scr.new_track(self.current_track)
        self.app.screen_manager.current = 'Player'


SCREENS = { 0: (MainScreen, 'Main'),
            1: (Albums, 'Albums'),
            2: (Player, 'Player'),
            3: (Tracks, 'Tracks')}


class MusicPlayerApp(App):
    """def build(self):
        return MusicPlayerOri()
    """

    def build(self):
        """Exécuté après build_config, construit les écrans
        Pour chaque écran, équivaut à
            self.screen_manager.add_widget(MainScreen(name="Main"))
        """
        Window.clearcolor = (1, 1, 1, 1)

        self.screen_manager = ScreenManager()
        for i in range(len(SCREENS)):
            self.screen_manager.add_widget(SCREENS[i][0](name=SCREENS[i][1]))
        return self.screen_manager

    def build_config(self, config):
        print("Création du fichier *.ini si il n'existe pas")
        config.setdefaults( 'library', {'path': '/home/pi'})
        print("self.config peut maintenant être appelé")

    def build_settings(self, settings):
        """Construit l'interface de l'écran Options, pour MusicPlayer seul,
        Les réglages Kivy sont par défaut.
        Cette méthode est appelée par app.open_settings() dans .kv,
        donc si Options est cliqué !
        """

        print("Construction de l'écran Options")

        data = """[ {"type": "title", "title": "Music Player"},

                        {"type": "string",
                         "title": "Bibliothèque",
                         "desc": "Chemin versla bibliothèque",
                         "section": "library",
                         "key": "path"}
                    ]"""

        # self.config est le config de build_config
        settings.add_json_panel('MusicPlayer', self.config, data=data)

    def go_mainscreen(self):
        """Retour au menu principal depuis les autres écrans."""
        self.screen_manager.current = ("Main")

    def do_quit(self):
        # Kivy
        print("Quit final")
        MusicPlayerApp.get_running_app().stop()


MusicPlayerApp().run()
