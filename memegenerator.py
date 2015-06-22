from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
from telex import plugin
from tempfile import mkstemp

import json
import glob
import os
import random
import tgl


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(THIS_DIR, "Impact.ttf")
# MEME_DIR = os.path.join(THIS_DIR, "memes")
MEME_DIR = os.path.join(THIS_DIR, "apimeme")
INVALID_DIR = os.path.join(THIS_DIR, "invalid")
INVALID_FILES = glob.glob(os.path.join(INVALID_DIR, "*.jpg"))

MEME_NAME_MAP = {}
with open(os.path.join(THIS_DIR, "mapping.json"), "r") as f:
    MEME_NAME_MAP = json.loads(f.read())

MEME_NAMES = MEME_NAME_MAP.keys()


class MemeGeneratorPlugin(plugin.TelexPlugin):
    """
    Generates memes using builting images and user input
    """

    patterns = {
        "^{prefix}memelist$": "list_memes",
        "^{prefix}argumentinvalid$": "argument_invalid",
        '^{prefix}memesearch (\w+)$': "search_memes",
        '^{prefix}meme\s*(?P<meme_name>\w+)\s*(?:"(?P<top_text>\w*)")*\s*(?:"(?P<bottom_text>\w*)")*$': "make_meme",
    }

    usage = [
        "{prefix}memelist : lists available memes",
        "{prefix}memesearch (x): searches within available memes for meme which has x in its name",
        "{prefix}argumentinvalid : gets a random 'argument invalid' meme",
        "{prefix}meme (memename) \"(top text)\" \"(bottom text)\" : makes beautiful meme. Quotes are mandatory",
    ]

    def list_memes(self, msg, matches):
        peer = self.bot.get_peer_to_send(msg)
        text = "Please refer to: https://github.com/maikelwever/telex-memegenerator/tree/master/apimeme"
        peer.send_msg(text, reply=msg.id, preview=False)

    def search_memes(self, msg, matches):
        peer = self.bot.get_peer_to_send(msg)
        query = matches.group(1)

        text = "\n".join(name for name in MEME_NAMES if query in name)
        if not text:
            text = "Not found :("

        peer.send_msg(text, reply=msg.id, preview=False)

    def argument_invalid(self, msg, matches=None):
        peer = self.bot.get_peer_to_send(msg)
        filename = random.choice(INVALID_FILES)
        tgl.send_photo(peer, filename)

    def make_meme(self, msg, matches):
        groupdict = matches.groupdict()

        meme_name = groupdict['meme_name'].lower()
        top_text = groupdict['top_text'] or ""
        bottom_text = groupdict['bottom_text'] or ""
        top_text = top_text.upper()
        bottom_text = bottom_text.upper()

        if meme_name not in MEME_NAMES:
            return self.argument_invalid(msg)

        img = Image.open(os.path.join(THIS_DIR, MEME_DIR, MEME_NAME_MAP[meme_name]))
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
