
import os
from pathlib import Path
import json
from collections import OrderedDict

import mutagen
from mutagen.flac import Picture, FLAC


def get_lib_infos(library, current_dir):
    """Parcours le dossier library,
    trouve les dossiers albums, avec des fichiers .flac
    Retourne un dict:
    l = {'nom du dossier parent': {'album': 'toto',
                                   'artist':,
                                   'cover':,
                                   'titres': { 0: ('tata','chemin abs',lenght),
                                               1: ('titi','chemin abs',lenght)}}}
    l et 'titres' sont des un OrderedDict
    """
    lib_infos = {}
    for root, directories, fichiers in os.walk(library):
        for fichier in fichiers:
            # num sert si pas de tracknumber
            num = 0
            if fichier.endswith(".flac"):
                fichier_abs = os.path.join(root, fichier)
                # # print("Fichier trouvé:", fichier_abs, "\n   ", fichier)

                album_name = str(Path(fichier_abs).parent)

                title, album, artist, cover, tracknumber, lenght = \
                                        fichier_information(fichier_abs,
                                                            num,
                                                            current_dir)

                if album_name not in lib_infos:
                    lib_infos[album_name] = {}

                if 'album' not in lib_infos[album_name]:
                    lib_infos[album_name]['album'] = album

                if 'artist' not in lib_infos[album_name]:
                    lib_infos[album_name]['artist'] = artist

                if 'cover' not in lib_infos[album_name]:
                    lib_infos[album_name]['cover'] = cover

                if 'titres' not in lib_infos[album_name]:
                    lib_infos[album_name]['titres'] = {}

                # Ajout des titres
                lib_infos[album_name]['titres'][tracknumber] = (title,
                                                                fichier_abs,
                                                                lenght)
                num += 1

    return lib_infos

def dict_to_OrderdDict(dico):

    order_of_keys = sorted([x for x in dico.keys()])
    list_of_tuples = [(key, dico[key]) for key in order_of_keys]
    ordered_dict = OrderedDict(list_of_tuples)
    return ordered_dict


def print_lib_infos(lib_infos):
    """Le json met les int en str"""
    print(json.dumps(lib_infos, sort_keys=False, indent=4))


def fichier_information(fichier, num, current_dir):
    """Informations sur un fichier"""

    song = mutagen.File(fichier)
    file_extension = str(type(song))

    # if file is FLAC, extract meta data
    if 'mutagen.flac.FLAC' in file_extension:

        try:
            tracknumber = song['TRACKNUMBER'][0]
        except KeyError:
            tracknumber = num

        try:
            title = str(song['TITLE'][0])
        except KeyError:
            title = 'unknown'

        try:
            album = str(song['ALBUM'][0])
        except KeyError:
            album = 'unknown'

        try:
            artist = str(song['ARTIST'][0])
        except KeyError:
            artist = 'unknown'

        try:
            lenght = str(song['LENGHT'][0])
        except KeyError:
            lenght = 60

        try:
            artwork = FLAC(fichier).pictures
            if artwork:
                if artwork[0].mime == 'image/jpeg':
                    cover = current_dir + '/covers/' + album + '.jpg'
                elif artwork[0].mime == 'image/png':
                    cover = current_dir + '/covers/' + album + '.png'
                p = Path(cover)
                if not p.is_file():
                    with open(cover, 'wb') as img:
                        img.write(artwork[0].data)
                        print(f"Save of cover: {cover}")
        except KeyError:
            cover = "covers/default_cover.png"

    return title, album, artist, cover, int(tracknumber), lenght


def get_tracks(lib_infos, album_key):
    """
    l = {'album_key':{ 'album': 'toto',
                                'artist':,
                                'cover':,
                                'titres': { 1: ('tata', 'chemin abs', lenght),
                                            2: ('titi', 'chemin abs', lenght)}}}
    """
    keys = sorted(list(lib_infos[album_key]['titres'].keys()))

    tracks = OrderedDict()
    # Un dict ordonné conserve l'ordre des clés de la création
    for item in keys:
        tracks[item] = lib_infos[album_key]['titres'][item]
    # # print(tracks)
    return tracks




if __name__ == '__main__':
    lib_infos = get_lib_infos('/media/data/3D/music')
    # # print_lib_infos(lib_infos)
    get_tracks(lib_infos, '/media/data/3D/music/flacs/Vieux_Farka_Tour\u00e9_Samba')
