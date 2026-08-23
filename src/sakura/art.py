"""The recovered picture.

Every glyph and all 29 colours were read back out of the original artwork, an
image that was itself a rendered ASCII grid: it could be measured (70x125 px
cells) and each cell matched against a template. The reconstruction is exact --
re-rendering this grid reproduced that image pixel for pixel, which is why the
image itself is no longer kept in the tree. It is in git history, at
``git show 6f10f12:src/sakura-original.png``.

ART    the characters, 26 rows of 62 columns
COLOR  a palette index per cell, chr(33 + i); ' ' where the cell is blank
LAYER  what each cell is: 'p' pot, 'w' wood, 'f' blossom, ' ' blank
"""

PALETTE = (
    '#c8ebb0', '#f8c8d0', '#f5b0bd', '#e38aae', '#a4c98a', '#f3a9c6',
    '#fbbac6', '#d6f0be', '#f7a2b5', '#8cb873', '#f395a6', '#7b5c50',
    '#efa0c4', '#9c7b6d', '#e6f7d8', '#b6dca0', '#b99588', '#6e4c42',
    '#5a4037', '#9b82b4', '#69614b', '#4d5c37', '#62533c', '#5c4f34',
    '#556140', '#596846', '#6e5f8c', '#9173a5', '#826ea0',
)

ART = (
    '                            %    #                            ',
    '               %          &%#@ #%#%                           ',
    '            &  &@&#  %&&&@#&&;%%% @@%@#                       ',
    '           #@#@%&@%&#%&#&&@%%@&@@%%#%   %                     ',
    '   %    @&#@@:@@#&&%@ ##@#%@@@#%&%@%&@&%&@                    ',
    '   # ##&&%%&&&&#%&%\\ ##=#@@&%@|_###|%@&&@#@   #&              ',
    '@&%@\\@#&#%#%#@%# ## \\@##&%&@@   |@@@&%&&@##& %###@&&   &      ',
    '&# %&\\@@#@%\\& @#     ||@&&%&&%  @ @@&@@%#&#%&%|_&#%%  @%@@    ',
    '&%#&#&&#%@& \\=_~______; &@  @&   @  _%&#@&@%@&@&%#&%%@@@@@@   ',
    ' %@   &@%             _|___     | :=%@::_:_#&#&##%:%&#&&&%    ',
    '                          ||   ::=_~~@%@&;%@&&#%&%% @%@#;&##  ',
    '                            |=|  &@@&#@@#%#%@%% @ = &&&#&&##  ',
    '                             :;  &@#%@%#%&#&% %  __%&&#&@%@%% ',
    '                              ||  #&&%##@@%&  _/   @#@&%#%&%@%',
    '                               ||#@%&%%;_=_%~\\    &%@&##~&%&&@',
    '                               =||  ~~        \\|_:%#&@##%%#@# ',
    '                               ||: //          |_#@%:#@%%&%& &',
    '                               ||//        %  @&#&&&&&@@%#&%  ',
    '                              |//         @@%&@@@#@%@###%&%   ',
    '                              |||          #@   %% &# ## %    ',
    '                              :~=                #%    %      ',
    '                              |:;                             ',
    '                  .___.__,._-/|||\\-.-.---.._.                 ',
    '                   \\                       /                  ',
    '                    \\_____________________/                   ',
    '                      _                 _                     ',
)

COLOR = (
    '                            !    "                            ',
    '               "          #$%& \'$#%                           ',
    '            (  #"#$  ))*!#++\',-++ &##)&                       ',
    '           $\'&\'"+$(+)\'$++-$)"+&+-)"$"   "                     ',
    '   &    &&))+.+!)++$& $-"+\'\')/+0-$\'\'#"#+\')                    ',
    '   \' "$"%)#)""&&\'\'#1 "#2$)"$-#2.)$$3)""+-"/   )&              ',
    '-\'&(."-&&"\'($\')# +& 2-!$--*%+   .)#&++$)+#"" \'$-+#""   \'      ',
    '\'/ "#.&+++"2( $"     .1!)&+)\'(  + $-+-$\'%+)\'\'-31&-\'-  -$++    ',
    '*-+-#-*&((! 31121323122 +"  )$   \'  1+++&#)*)&)#--#+/&&)&&(   ',
    ' ")   )-#             ,1,22     3 .,+"33232")&+!&#10"&#%$"    ',
    '                          1,   ,3,121++#\'1)+\'\'-$(-& $#"&3+\'"  ',
    '                            3.3  *#&\'#($/""$$## " 2 +-+-"$&#  ',
    '                             23  #(-/"$\')#$"$ "  ,1-+-+/+&-)" ',
    '                              .3  &+)\'0)\'""/  32   (#"-!"-&-$"',
    '                               2,"$+)$#.,3.+1,    \'#*\'+",++#-#',
    '                               ,,1  ,3        1,3,$+")#"+&\'$" ',
    '                               31. 31          ,3#$&.)\'+"&"* )',
    '                               ,,13        +  )$"-)#"--"&#\'&  ',
    '                              ,3.         #")$\'*!&+#&-$++&&   ',
    '                              332          \'"   "- +( $# $    ',
    '                              3,.                )#    +      ',
    '                              332                             ',
    '                  45667789786333,.96658:6:754                 ',
    '                   4                       ;                  ',
    '                    <44;=<;4;<;==;<<4;;<4;<                   ',
    '                      =                 =                     ',
)

LAYER = (
    '                            f    f                            ',
    '               f          ffff ffff                           ',
    '            f  ffff  ffffffffwfff fffff                       ',
    '           ffffffffffffffffffffffffff   f                     ',
    '   f    fffffwfffffff ffffffffffffffffffff                    ',
    '   f ffffffffffffffw ffwffffffwwfffwfffffff   ff              ',
    'ffffwfffffffffff ff wffffffff   wfffffffffff fffffff   f      ',
    'ff ffwfffffwf ff     wwfffffff  f ffffffffffffwwffff  ffff    ',
    'fffffffffff wwwwwwwwwww ff  ff   f  wffffffffffffffffffffff   ',
    ' ff   fff             wwwww     w wwffwwwwwfffffffwfffffff    ',
    '                          ww   wwwwwwffffwfffffffff ffffwfff  ',
    '                            www  ffffffffffffff f w ffffffff  ',
    '                             ww  ffffffffffff f  wwffffffffff ',
    '                              ww  ffffffffff  ww   fffffffffff',
    '                               wwffffffwwwwfww    ffffffwfffff',
    '                               www  ww        wwwwfffffffffff ',
    '                               www ww          wwfffwfffffff f',
    '                               wwww        f  ffffffffffffff  ',
    '                              www         fffffffffffffffff   ',
    '                              www          ff   ff ff ff f    ',
    '                              www                ff    f      ',
    '                              www                             ',
    '                  pppppppppppwwwwwppppppppppp                 ',
    '                   p                       p                  ',
    '                    ppppppppppppppppppppppp                   ',
    '                      p                 p                     ',
)

ROWS = len(ART)
COLS = len(ART[0])
