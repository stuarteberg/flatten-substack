#!/bin/bash

slab={{ cookiecutter.tab_name }}
basePath={{ cookiecutter.substack_base_dir }}
resultDataFolder=flatten
resultDataPath=${basePath}/${resultDataFolder}
origDataPath={{ cookiecutter.substack_slice_dir }}

amiraPath="/groups/flyem/data/alignment/Amira-6.5.0"
amiralocal="/groups/flyem/data/alignment/facefinder"

amiraScriptDir=$amiralocal/src/hxadjustheightsurf/share/scripts
clusterscriptdir=$amiraScriptDir
export ZIBAMIRA=$amiraPath/bin/arch-LinuxAMD64-Optimize/Amira
vncDir=$amiralocal
maxNumJobs=10

# Is this correct?
# Examples use section name: group="/flyem/Z1217_19m/Sec03"
# but maybe an arbitrary name (such as the substack_name) is fine here... 
group="/{{ cookiecutter.bill_to }}/{{ cookiecutter.fly }}/{{ cookiecutter.substack_name }}"
