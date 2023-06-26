#!/bin/bash

basedir="/media/Data02/SoCoStim/SimNIBS"
subs=$(find $basedir/S* -maxdepth 0 -exec basename {} \;)

if [ ! -d "$basedir/Code/freeview_check" ]; then
    mkdir "$basedir/Code/freeview_check"
fi

for sub in $subs; do
    freeview -v "$basedir/$sub/m2m_SimNIBS4_$sub/T1.nii.gz" \
    -v "$basedir/$sub/m2m_SimNIBS4_$sub/final_tissues.nii.gz:colormap=lut:lut=$basedir/$sub/m2m_SimNIBS4_$sub/final_tissues_LUT.txt:outline=true" \
    --viewport z -zoom 1.3 -ras 0 30 0 tkreg --screenshot "$basedir/Code/freeview_check/${sub}_charm.png"
    
done