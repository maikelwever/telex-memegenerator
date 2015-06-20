from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
from telex import plugin
from tempfile import mkstemp

import glob
import os
import random
import tgl


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(THIS_DIR, "Impact.ttf")
MEME_DIR = os.path.join(THIS_DIR, "memes")
INVALID_DIR = os.path.join(THIS_DIR, "invalid")
INVALID_FILES = glob.glob(os.path.join(INVALID_DIR, "*.jpg"))


class MemeGeneratorPlugin(plugin.TelexPlugin):
    """
    Generates memes using builting images and user input
    """

    patterns = {
        "^{prefix}memelist$": "list_memes",
        "^{prefix}argumentinvalid$": "argument_invalid",
        '^{prefix}meme (?P<meme_name>[\w\d]+) (?P<top_text>".+") (?P<bottom_text>".*")$': "make_meme",
        '^{prefix}meme (?P<meme_name>[\w\d]+) (?P<bottom_text>".*")$': "make_meme",
    }

    usage = [
        "{prefix}memelist : lists available memes",
        "{prefix}argumentinvalid : gets a random 'argument invalid' meme",
        "{prefix}meme (memename) \"(top text)\" \"(bottom text)\" : makes beautiful meme. Quotes are mandatory",
    ]

    meme_name_map = {
        "skiinstructor": "skiinstructor.png",
        "aliens": "aliens.jpg",
        "sap": "sap.jpg",
        "successkid": "successkid.jpg",
    }

    def list_memes(self, msg, matches):
        peer = self.bot.get_peer_to_send(msg)
        memes_string = "Available memes:\n - " + "\n - ".join(self.meme_name_map.keys())
        peer.send_msg(memes_string, reply=msg.id, preview=False)

    def argument_invalid(self, msg, matches=None):
        peer = self.bot.get_peer_to_send(msg)
        filename = random.choice(INVALID_FILES)
        tgl.send_photo(peer, filename)

    def make_meme(self, msg, matches):
        groupdict = matches.groupdict()
        groups = groupdict.keys()

        if 'top_text' in groups:
            top_text = groupdict['top_text'].strip('"').upper()
        else:
            top_text = ""

        meme_name = groupdict['meme_name'].lower()
        bottom_text = groupdict['bottom_text'].strip('"').upper()

        if meme_name not in self.meme_name_map.keys():
            return self.argument_invalid(msg)

        img = Image.open(os.path.join(THIS_DIR, MEME_DIR, self.meme_name_map[meme_name]))
        image_size = img.size

        # find biggest possible font size
        font_size = int(image_size[1]/5)
        font = ImageFont.truetype(FONT_FILE, font_size)
        top_text_size = font.getsize(top_text)
        bottom_text_size = font.getsize(bottom_text)
        while top_text_size[0] > image_size[0]-20 or bottom_text_size[0] > image_size[0]-20:
            font_size = font_size - 1
            font = ImageFont.truetype(FONT_FILE, font_size)
            top_text_size = font.getsize(top_text)
            bottom_text_size = font.getsize(bottom_text)

        # position top text
        top_text_position_x = (image_size[0]/2) - (top_text_size[0]/2)
        top_text_position_y = 0
        top_text_position = (top_text_position_x, top_text_position_y)

        # position bottom text
        bottom_text_position_x = (image_size[0]/2) - (bottom_text_size[0]/2)
        bottom_text_position_y = image_size[1] - bottom_text_size[1]
        bottom_text_position = (bottom_text_position_x, bottom_text_position_y)

        draw = ImageDraw.Draw(img)

        # draw outlines
        # there may be a better way
        outline_range = int(font_size/15)
        for x in range(outline_range - 1, outline_range + 1):
            for y in range(outline_range - 1, outline_range + 1):
                draw.text((top_text_position[0] + x, top_text_position[1] + y),
                          top_text, (0, 0, 0), font=font)
                draw.text((bottom_text_position[0] + x, bottom_text_position[1] + y),
                          bottom_text, (0, 0, 0), font=font)

        draw.text(top_text_position, top_text, (255, 255, 255), font=font)
        draw.text(bottom_text_position, bottom_text, (255, 255, 255), font=font)

        filename = mkstemp(suffix='.png', prefix="telex-memeplugin-")[1]
        img.save(filename, 'png')

        peer = self.bot.get_peer_to_send(msg)

        def cleanup_cb(success, msg):
            if success:
                os.remove(filename)
            else:
                return self.argument_invalid(msg)

        tgl.send_photo(peer, filename, cleanup_cb)
