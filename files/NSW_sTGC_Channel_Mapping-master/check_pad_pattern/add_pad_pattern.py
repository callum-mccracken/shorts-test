# This script add a column to the mapping.txt file for the pad patterns.
# The output file is mapping_patterns.txt
# The scripts simply reads the current mapping.txt and uses the 'CheckPadPattern' utility.

import subprocess

# import the mapping file
with open("../mapping.txt") as textFile:
    mapping = [line.split() for line in textFile]


f = open("mapping_patterns.txt","w+")
delimiter='\t'
for row in mapping:
    # First part of each row written as-is
    new_line = delimiter.join(row[0:13])
    f.write(new_line)

    # Now get the pad pattern for each pad channel
    if row[3] == 'pad':
        pattern = subprocess.check_output(["./CheckPadPattern", row[0], '-GV'+row[1], row[6], '--batch-mode'])
        print(row[0], 'GV'+row[1], 'ID'+row[6], '->', pattern)
        pattern_ascii = pattern.decode('ascii')
        if pattern_ascii == '-\n':
            pattern_ascii = 'n.a.\n'
        f.write('\t'+pattern_ascii)
    else:
        f.write('\tn.a.\n')


f.close()

    
    
