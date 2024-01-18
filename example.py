# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 20:17:00 2024

@author: nanashi
"""

import ss_bomberman as ssb

#%% Convert TALKCHR to PNG images

# VS.BIN contains a list with all images and palette indices
image_list = ssb.read_image_lst("VS.bin")
palette_list = ssb.read_palette_lst("VS.bin")
# TALKCOL.BIN contains the color palette data
pal_lut = ssb.talkcol2lut("TALKCOL.BIN", palette_list)
# TALKCHR.BIN contains the image data
ssb.talkchr2png("TALKCHR.BIN", "images/", image_list, palette_list, pal_lut)
        
#%% Change text of dialogs in game

# Read the original TALKANM.BIN
text, unk, ptr = ssb.read_talkanm("TALKANM.BIN", 33634, 778)

# New dialog
dialog = ["What? So I've got you first, Kuro!",
          "Just my luck, you from the start"]

# Convert the new text to lists of ascii indices
insert = []
for dial in dialog:
    insert.append([])
    for c in dial:
        insert[-1].append(int().from_bytes(c.encode("ascii"), 'big'))
      
# Insert the new text inbetween the control codes
# Control code positions must be manually selected
# First control codes are 0, 0, 4
# I don't know what the first two do, but 4 is the delay between characters printed
# Decrease to speed up the following textbox
old = text
text = [0, 0, 4]+insert[0]+[65535, 1, 1, 4]+insert[1]+text[44:]

# Construct a new TALKANM.BIN
fpos = ssb.write_talkanm("TALKANM_new.BIN", text, unk)

# The values at 0x22598 and 0x2259C in VS.BIN must be overwritten with this "fpos" otherwise the text breaks.
# These are pointers to the position of the pointer table at the end of "TALKANM.BIN". Since we change the
# size it must updated.
print(hex(fpos))
