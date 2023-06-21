#!/bin/bash

basedir="/media/Data02/SoCoStim/SimNIBS"
subs=$(find $basedir/S* -maxdepth 0 -exec basename {} \;)

for sub in $subs; do
    
    # do not process already processed files
    if [ -d "$basedir/$sub/m2m_SimNIBS4_$sub" ]; then
        continue
    fi
    
    t1="$basedir/$sub/rT1w.nii.gz"
    t2="$basedir/$sub/rT2w.nii.gz"
    
    if [ -f "$t1" ] && [ -f "$t2" ]; then
        cd "$basedir/$sub" || exit
        
        echo "###########################"
        echo "$sub"
        echo "###########################"
        
        charm "SimNIBS4_$sub" "$t1" "$t2" --forceqform
        elif [ -f "$t1" ]; then
        cd "$basedir/$sub" || exit
        echo "###########################"
        echo "$sub"
        echo "###########################"
        
        charm "SimNIBS4_$sub" "$t1" --forceqform
    fi
    
done
