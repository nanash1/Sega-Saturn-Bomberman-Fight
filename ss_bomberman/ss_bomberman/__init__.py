# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 19:23:16 2020

@author: nanashi
"""

import ntpath
import PIL as pil
import numpy as np

def _plt2clut(plt_data, bpp):
    """
    Converts palette from *.plt file to RGB color lut

    Parameters
    ----------
    plt_data : byte-like
        Raw palette data.
    bpp : int
        Bit per pixel.

    Returns
    -------
    RGB color lut.

    """
    palette_size = 2**bpp
    rgb_clut = []
    j = 0
    for i in range(0,palette_size):
    
        rgb_clut_triplet = [0, 0, 0]
        color = (plt_data[j] >> 2) & 31
        color = int(color*8)
        rgb_clut_triplet[2] = color
        
        color = ((plt_data[j] & 3) << 3) | (plt_data[j+1] >> 5)
        color = int(color*8)
        rgb_clut_triplet[1] = color
        
        color =  plt_data[j+1] & 31
        color = int(color*8)
        rgb_clut_triplet[0] = color
        
        rgb_clut.append(rgb_clut_triplet)
        
        j += 2
        
    return rgb_clut

def _bin2rgb(image_bin, rgb_clut, width, height, bpp):
    """
    Converts binary image with indexed colors to an RGB image

    Parameters
    ----------
    image_bin : byte-like
        Image data as indexed colors.
    rgb_clut : list
        Color lut.
    width : int
        Image width in px.
    height : int
        Image height in px.
    bpp : int
        Bit per pixel.

    Returns
    -------
    image_rgb : byte-like
        Image RGB data.

    """
    image_rgb = bytes()
    for i in range(0,int(width*height*(bpp/8))):
        if bpp == 8:
            index = image_bin[i]
            image_rgb +=  rgb_clut[index][0].to_bytes(1, 'big')
            image_rgb +=  rgb_clut[index][1].to_bytes(1, 'big')
            image_rgb +=  rgb_clut[index][2].to_bytes(1, 'big')
        elif bpp == 4:
            index = (image_bin[i] & 240) >> 4
            image_rgb +=  rgb_clut[index][0].to_bytes(1, 'big')
            image_rgb +=  rgb_clut[index][1].to_bytes(1, 'big')
            image_rgb +=  rgb_clut[index][2].to_bytes(1, 'big')
            index = image_bin[i] & 15
            image_rgb +=  rgb_clut[index][0].to_bytes(1, 'big')
            image_rgb +=  rgb_clut[index][1].to_bytes(1, 'big')
            image_rgb +=  rgb_clut[index][2].to_bytes(1, 'big')
    return image_rgb
    
def read_image_lst(file, entries=812):
    '''
    Reads the list of images from VS.BIN

    Parameters
    ----------
    file : str
        VS.BIN.
    entries : int, optional
        Number images in the list. The default is 812.

    Returns
    -------
    image_list : list
        list with image data (scale, address, size).

    '''
    vs_offset = 0x1AAB0
    image_list = []
    with open(file, 'rb') as in_file:
        in_file.seek(vs_offset)
        line = in_file.read(8)
        while entries:
            x_scale = int.from_bytes(line[0:2], byteorder='big')
            y_scale = int.from_bytes(line[2:4], byteorder='big')
            address = int.from_bytes(line[4:6], byteorder='big')
            x_size = int.from_bytes(line[6:7], byteorder='big')
            y_size = int.from_bytes(line[7:8], byteorder='big')
            image_list.append(((x_scale, y_scale), address, (x_size*8, y_size)))
            line = in_file.read(8)
            entries -= 1
            
    return image_list

def read_palette_lst(file, entries=812):
    '''
    Reads the palette list from VS.BIN

    Parameters
    ----------
    file : str
        VS.BIN.
    entries : int, optional
        Number images in the list. The default is 812.

    Returns
    -------
    palette_list : list
        List of palette indices.

    '''
    vs_offset = 0x1C410
    palette_list = []
    with open(file, 'rb') as in_file:
        in_file.seek(vs_offset)
        line = in_file.read(4)
        while entries:
            palette_list.append(int.from_bytes(line[0:2], byteorder='big') >> 4)
            line = in_file.read(4)
            entries -= 1
            
    return palette_list

def talkcol2lut(file, palette_lst):
    '''
    Reads palettes from TALKCOL.BIN and creates a LUT. 

    Parameters
    ----------
    file : str
        TALKCOL.BIN.
    palette_lst : list
        List generated from VS.BIN by read_palette_lst.

    Returns
    -------
    palette_lut : dict.
        Palette LUT.

    '''
    palette_lut = {}
    with open(file, 'rb') as in_file:
        raw = in_file.read()
        for pal in palette_lst:
            start = (pal*0x20)-0x200                                           # palettes are 0x20 bytes long, in the TALKCOL.BIN file they
            end = start + 0x20                                                 # are offset by 0x200 for some reason
            if pal not in palette_lut:
                palette_lut[pal] = raw[start:end]
                
    return palette_lut
    
def talkchr2png(file, folder, image_list, palette_list, palette_lut):
    '''
    Converts TALKCHR.BIN to PNG images.

    Parameters
    ----------
    file : str
        TALKCHR.BIN.
    folder : str
        Output folder.
    image_list : list
        List generated from VS.BIN by read_image_lst.
    palette_list : list
        List generated from VS.BIN by read_palette_lst.
    palette_lut : list
        LUT generated from TALKCOL.BIN by talkcol2lut.

    Returns
    -------
    None.

    '''
    with open(file, 'rb') as in_file:
        cntr = 0
        ptr = 0
        talkchr_ptr = []
        for scale, address, size in image_list:
            bsize = (size[0]*size[1]) // 2
            rgb_clut = _plt2clut(palette_lut[palette_list[cntr]], 4)
            image_raw = in_file.read(bsize)
            talkchr_ptr.append(ptr)
            ptr += bsize
            image_rgb = _bin2rgb(image_raw, rgb_clut, *size, 4)
            
            image = pil.Image.frombytes("RGB", size ,image_rgb)
            image.save(folder+f"{cntr:03}"+"image"+".png", "PNG")
            cntr += 1

def read_talkanm(file, text_len=33634, char_num=778):
    '''
    Converts TALKANM.BIN into Python data structures.

    Parameters
    ----------
    file : str
        TALKANM.BIN.
    text_len : int, optional
        Number of letters in TALKANM.BIN. The default is 33634.
    char_num : int, optional
        Number of different characters used for text. The default is 778.

    Returns
    -------
    text : list
        Letter indices of dialog text.
    sec2 : list
        Second part of file, struct with not completely known function.
    ptr : list
        List of pointers to section 2.

    '''
    with open(file, 'rb') as in_file:
        raw = in_file.read()
    
    text = []
    for i in range(text_len):
        text.append(int.from_bytes(raw[i*2:(i+1)*2], byteorder='big'))
        
    base = text_len*2
    sec2 = []
    for i in range(char_num):
        off = i*12
        first = int.from_bytes(raw[base+off:base+off+4], byteorder='big')
        second = int.from_bytes(raw[base+off+4:base+off+8], byteorder='big')
        third = int.from_bytes(raw[base+off+8:base+off+12], byteorder='big')
        sec2.append((first, second, third))
        
    base = (text_len*2)+(char_num*12)
    ptr = []
    for i in range(char_num):
        ptr.append(int.from_bytes(raw[base+(i*4):base+((i+1)*4)], byteorder='big'))
        
    return text, sec2, ptr

def write_talkanm(file, text, sec2):
    '''
    Constructs a new TALKANM.BIN.

    Parameters
    ----------
    file : str
        Name for updated TALKANM.BIN.
    text : list
        Letter indices of dialog text.
    sec2 : list
        Second part of file, struct with not completely known function.

    Returns
    -------
    fpos : int
        New base address of pointer list.

    '''
    fpos = 0x2C0000
    raw = bytes()
    for t in text:
        raw += t.to_bytes(2, 'big')
        fpos += 2
        
    pad = fpos % 4
    if pad > 0:
        raw += b'\xff'*(4-pad)
        fpos += 4-pad
        
    ptr = []
    for first, second, third in sec2:
        ptr.append(fpos)
        raw += first.to_bytes(4, 'big')
        raw += second.to_bytes(4, 'big')
        raw += third.to_bytes(4, 'big')
        fpos += 12
        
    
    for p in ptr:
        raw += p.to_bytes(4, 'big')
    
    with open(file, 'wb') as out_file:
        out_file.write(raw)
        
    return fpos

