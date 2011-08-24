#!/bin/bash

function metasetup { 
    OLD_IFS=$IFS
    IFS=";
"
    for line in `python manage.py metasetup "$@"`
      do
      eval $line
    done
    IFS=$OLD_IFS
};

export -f metasetup
