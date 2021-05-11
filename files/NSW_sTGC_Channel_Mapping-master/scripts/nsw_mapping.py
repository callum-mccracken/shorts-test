import sys
from xml.etree import ElementTree as ET


def read_xml(node_path, xml_file_name):
    tree = ET.parse(xml_file_name)
    root = tree.getroot()
    node = root.find(node_path)
    return node.text


def get_board_type(gv, etype):
    if etype=='strip':
        if gv in [1,3]:
            return 'K13'
        elif gv in [2,4]:
            return 'K24'
    elif etype=='pad':
        if gv in [1,2]:
            return 'H12'
        elif gv in [3,4]:
            return 'H34'        
    elif etype=='wire':
        return 'W'+str(gv)
    return ''


def get_num_pad_rows(module, gv):
    xml_file = 'geometry/'+module+'.xml'
    board_type = get_board_type(gv, 'pad')
    xml_node = 'nPadRows_'+board_type
    return int(read_xml(xml_node, xml_file))


def get_num_channels_xml(module, gv, etype):
    if etype in ['strip', 'wire']:
        module = module[:3]
    elif etype == 'pad':
        module = module[:4]

    xml_file = 'geometry/'+module+'.xml'
    xml_node = 'nChannels_'+get_board_type(gv, etype)
    return int(read_xml(xml_node, xml_file))




class Channel:
    """Represents an electronic channel."""
    def __init__(self, mapping_row):
        self.module = mapping_row[0]
        self.gv = int(mapping_row[1])
        self.etype = mapping_row[3]
        self.qid = int(mapping_row[6])

    def to_tuple(self):
        return (self.module, self.gv, self.etype, self.qid)
    def __str__(self):
        return str(self.to_tuple());
    def __repr__(self):
        return str(self.to_tuple());

    
def get_num_channels(mapping):
    ch_list = [Channel(row) for row in mapping]
    sorted_ch_list = {}
    num_channels = {}
    for ch in ch_list:
        if ch.module not in sorted_ch_list:
            sorted_ch_list[ch.module] = {}
            num_channels[ch.module] = {}
        if ch.gv not in sorted_ch_list[ch.module]:
            sorted_ch_list[ch.module][ch.gv] = {}
            num_channels[ch.module][ch.gv] = {}
        if ch.etype not in sorted_ch_list[ch.module][ch.gv]:
            sorted_ch_list[ch.module][ch.gv][ch.etype] = []
            num_channels[ch.module][ch.gv][ch.etype] = 0

        sorted_ch_list[ch.module][ch.gv][ch.etype].append(ch.qid)


    for mod, l0 in sorted_ch_list.items():
        for gv, l1 in l0.items():
            for etype, ch_list in l1.items():
                if min(ch_list) != 1:
                    raise Exception('Invalid minimum channel in list.')
                N = len(ch_list)
                if max(ch_list) != N:
                    raise Exception('Invalid maximum channel in list.')
                if len(ch_list) != len(set(ch_list)):
                    raise Exception('Channel list has duplicated.')
                if get_num_channels_xml(mod,gv,etype)!=N:
                    raise Exception('Number of channels inconsistent with XML files.')
                num_channels[mod][gv][etype] = N                
    return num_channels


def get_pad_rows_columns():
    rows = {}
    cols = {}
    for size in ['S', 'L']:
        for logic in ['P', 'C']:
            for modID in [1,2,3]:
                mod = "Q"+size+str(modID)+logic
                rows[mod] = {}
                cols[mod] = {}
                for gv in [1,2,3,4]:
                    nrows = get_num_pad_rows(mod, gv)
                    nch = get_num_channels_xml(mod, gv, 'pad')
                    if (nch%nrows) != 0:
                        raise Exception('Invalid channel or row number.')
                    ncols = int(nch/nrows)
                    rows[mod][gv]=nrows
                    cols[mod][gv]=ncols
                    
    return rows, cols


def get_invertx_qid(ch, nch, prows, pcols):
    if ch.etype == 'wire':
        N = nch[ch.module][ch.gv][ch.etype]
        return (N-ch.qid+1)
    elif ch.etype == 'pad':
        #nrows = prows[ch.module][ch.gv]
        ncols = pcols[ch.module][ch.gv]
        row = int((ch.qid-1)/ncols)
        col = (ch.qid-1)%ncols
        col = ncols-col-1 # inversion here
        return row*ncols+col+1
    else:
        raise Exception('Invalid channel.')
    

    


# USAGE: python3 nsw_mapping.py [path/to/mapping/file.txt (default=../mapping.txt)]
if __name__ == '__main__':

    # Parse arguments
    print('**** NSW mapping ****')
    mapping_file_name = '../mapping.txt'
    if len(sys.argv)>1:
        mapping_file_name = sys.argv[1]

        
    # Transfert mapping file to memory
    print('Reading mapping file:', mapping_file_name)
    mapping = []
    mapping_file = open(mapping_file_name, 'r')
    for row in mapping_file:
        srow = row.split()
        if len(srow)>16:
            raise Exception('Corrupted mapping file.')
        while len(srow) != 16:
            srow.append('')
        mapping.append(srow)
    mapping_file.close()


    # Get info on number of channels, pad_rows and pad_columns
    print('Get channel info...')
    num_channels = get_num_channels(mapping) # mod->gv->etype->N 
    pad_rows, pad_columns = get_pad_rows_columns() # mod->gv->N


    # Calculate the new IDs for side A/C
    print('Calculate IDs for side A/C...')
    for row in mapping:
        ch = Channel(row)
        logic = ch.module[3]
        sideA_id=-1
        sideC_id=-1   
        if ch.etype=='strip':
            sideA_id = ch.qid
            sideC_id = ch.qid
        elif ch.etype in ['wire', 'pad']:
            if logic=='P':
                sideA_id = get_invertx_qid(ch, num_channels, pad_rows, pad_columns)
                sideC_id = ch.qid
            elif logic=='C':
                sideA_id = ch.qid
                sideC_id = get_invertx_qid(ch, num_channels, pad_rows, pad_columns)                

        if sideA_id<0 or sideC_id<0:
            raise Exception('Invalid new ID.')

        row[14] = sideA_id
        row[15] = sideC_id 
                
    
    # Export mapping to input file
    print('Saving new mapping to file...')
    fout = open("../new_mapping.txt", "w")
    for row in mapping:
        row_str = [str(val) for val in row]
        fout.write('\t'.join(row_str)+'\n')
    
    print('Goodbye!')
    exit(0)


    
    for row in mapping_file:
        srow = row.split()

        mod_type = srow[0]
        etype = srow[3]
        #gv = int(srow[1])
        quad_id = int(srow[6])
        logic = mod_type[3]
        

        if etype == 'strip':
            sideA_id = quad_id
            sideC_id = quad_id
        elif etype == 'wire':
            pass

        if sideA_id<=0 or sideC_id<=0:
            raise Exception('Invalid new ID.')
        

        
         #print("mod=%s, etype=%s, gv=%i, qid=%i" % (mod_type,etype,gv,quad_id))
        
        






    
     
