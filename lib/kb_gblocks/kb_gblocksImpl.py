# -*- coding: utf-8 -*-
#BEGIN_HEADER
import os
import sys
import shutil
import hashlib
import subprocess
import requests
import re
import traceback
import uuid
from datetime import datetime
from pprint import pprint, pformat
import numpy as np
import gzip

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.Alphabet import generic_protein
from biokbase.workspace.client import Workspace as workspaceService
from requests_toolbelt import MultipartEncoder
from biokbase.AbstractHandle.Client import AbstractHandle as HandleService
from DataFileUtil.DataFileUtilClient import DataFileUtil as DFUClient
from KBaseReport.KBaseReportClient import KBaseReport

# silence whining
import requests
requests.packages.urllib3.disable_warnings()
#END_HEADER


class kb_gblocks:
    '''
    Module Name:
    kb_gblocks

    Module Description:
    ** A KBase module: gblocks
**
** This module runs Gblocks trim Multiple Sequence Alignments (MSAs) to remove hypervariable (gappy) regions using Gblocks
**
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.2"
    GIT_URL = "https://github.com/dcchivian/kb_gblocks"
    GIT_COMMIT_HASH = "4fe789124fe5ecce2b2d05399f671f7ceb5dbb75"

    #BEGIN_CLASS_HEADER
    workspaceURL = None
    shockURL = None
    handleURL = None

    GBLOCKS_bin = '/kb/module/Gblocks'

    # target is a list for collecting log messages
    def log(self, target, message):
        # we should do something better here...
        if target is not None:
            target.append(message)
        print(message)
        sys.stdout.flush()

    def get_single_end_read_library(self, ws_data, ws_info, forward):
        pass

    def get_feature_set_seqs(self, ws_data, ws_info):
        pass

    def get_genome_feature_seqs(self, ws_data, ws_info):
        pass

    def get_genome_set_feature_seqs(self, ws_data, ws_info):
        pass

    # Helper script borrowed from the transform service, logger removed
    #
    def upload_file_to_shock(self,
                             console,  # DEBUG
                             shock_service_url = None,
                             filePath = None,
                             ssl_verify = True,
                             token = None):
        """
        Use HTTP multi-part POST to save a file to a SHOCK instance.
        """
        self.log(console,"UPLOADING FILE "+filePath+" TO SHOCK")

        if token is None:
            raise Exception("Authentication token required!")

        #build the header
        header = dict()
        header["Authorization"] = "Oauth {0}".format(token)
        if filePath is None:
            raise Exception("No file given for upload to SHOCK!")

        dataFile = open(os.path.abspath(filePath), 'rb')
        m = MultipartEncoder(fields={'upload': (os.path.split(filePath)[-1], dataFile)})
        header['Content-Type'] = m.content_type

        #logger.info("Sending {0} to {1}".format(filePath,shock_service_url))
        try:
            response = requests.post(shock_service_url + "/node", headers=header, data=m, allow_redirects=True, verify=ssl_verify)
            dataFile.close()
        except:
            dataFile.close()
            raise
        if not response.ok:
            response.raise_for_status()
        result = response.json()
        if result['error']:
            raise Exception(result['error'][0])
        else:
            return result["data"]


    def upload_SingleEndLibrary_to_shock_and_ws (self,
                                                 ctx,
                                                 console,  # DEBUG
                                                 workspace_name,
                                                 obj_name,
                                                 file_path,
                                                 provenance,
                                                 sequencing_tech):

        self.log(console,'UPLOADING FILE '+file_path+' TO '+workspace_name+'/'+obj_name)

        # 1) upload files to shock
        token = ctx['token']
        forward_shock_file = self.upload_file_to_shock(
            console,  # DEBUG
            shock_service_url = self.shockURL,
            filePath = file_path,
            token = token
            )
        #pprint(forward_shock_file)
        self.log(console,'SHOCK UPLOAD DONE')

        # 2) create handle
        self.log(console,'GETTING HANDLE')
        hs = HandleService(url=self.handleURL, token=token)
        forward_handle = hs.persist_handle({
                                        'id' : forward_shock_file['id'], 
                                        'type' : 'shock',
                                        'url' : self.shockURL,
                                        'file_name': forward_shock_file['file']['name'],
                                        'remote_md5': forward_shock_file['file']['checksum']['md5']})

        
        # 3) save to WS
        self.log(console,'SAVING TO WORKSPACE')
        single_end_library = {
            'lib': {
                'file': {
                    'hid':forward_handle,
                    'file_name': forward_shock_file['file']['name'],
                    'id': forward_shock_file['id'],
                    'url': self.shockURL,
                    'type':'shock',
                    'remote_md5':forward_shock_file['file']['checksum']['md5']
                },
                'encoding':'UTF8',
                'type':'fasta',
                'size':forward_shock_file['file']['size']
            },
            'sequencing_tech':sequencing_tech
        }
        self.log(console,'GETTING WORKSPACE SERVICE OBJECT')
        ws = workspaceService(self.workspaceURL, token=ctx['token'])
        self.log(console,'SAVE OPERATION...')
        new_obj_info = ws.save_objects({
                        'workspace':workspace_name,
                        'objects':[
                            {
                                'type':'KBaseFile.SingleEndLibrary',
                                'data':single_end_library,
                                'name':obj_name,
                                'meta':{},
                                'provenance':provenance
                            }]
                        })[0]
        self.log(console,'SAVED TO WORKSPACE')

        return new_obj_info[0]

    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.workspaceURL = config['workspace-url']
        self.shockURL = config['shock-url']
        self.handleURL = config['handle-service-url']
        self.serviceWizardURL = config['service-wizard-url']

        self.callbackURL = os.environ.get('SDK_CALLBACK_URL')
        if self.callbackURL == None:
            raise ValueError ("SDK_CALLBACK_URL not set in environment")

        self.scratch = os.path.abspath(config['scratch'])
        # HACK!! temporary hack for issue where megahit fails on mac because of silent named pipe error
        #self.host_scratch = self.scratch
        #self.scratch = os.path.join('/kb','module','local_scratch')
        # end hack
        if not os.path.exists(self.scratch):
            os.makedirs(self.scratch)

        #END_CONSTRUCTOR
        pass


    def run_Gblocks(self, ctx, params):
        """
        Method for trimming MSAs of either DNA or PROTEIN sequences
        **
        **        input_type: MSA
        **        output_type: MSA
        :param params: instance of type "Gblocks_Params" (Gblocks Input
           Params) -> structure: parameter "workspace_name" of type
           "workspace_name" (** The workspace object refs are of form: ** ** 
           objects = ws.get_objects([{'ref':
           params['workspace_id']+'/'+params['obj_name']}]) ** ** "ref" means
           the entire name combining the workspace id and the object name **
           "id" is a numerical identifier of the workspace or object, and
           should just be used for workspace ** "name" is a string identifier
           of a workspace or object.  This is received from Narrative.),
           parameter "desc" of String, parameter "input_ref" of type
           "data_obj_ref", parameter "output_name" of type "data_obj_name",
           parameter "trim_level" of Long, parameter "min_seqs_for_conserved"
           of Long, parameter "min_seqs_for_flank" of Long, parameter
           "max_pos_contig_nonconserved" of Long, parameter "min_block_len"
           of Long, parameter "remove_mask_positions_flag" of Long
        :returns: instance of type "Gblocks_Output" (Gblocks Output) ->
           structure: parameter "report_name" of type "data_obj_name",
           parameter "report_ref" of type "data_obj_ref"
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN run_Gblocks
        console = []
        invalid_msgs = []
        self.log(console,'Running run_Gblocks with params=')
        self.log(console, "\n"+pformat(params))
        report = ''
#        report = 'Running run_Gblocks with params='
#        report += "\n"+pformat(params)


        #### do some basic checks
        #
        if 'workspace_name' not in params:
            raise ValueError('workspace_name parameter is required')
        if 'input_ref' not in params:
            raise ValueError('input_ref parameter is required')
        if 'output_name' not in params:
            raise ValueError('output_name parameter is required')


        #### Get the input_ref MSA object
        ##
        try:
            ws = workspaceService(self.workspaceURL, token=ctx['token'])
            objects = ws.get_objects([{'ref': params['input_ref']}])
            data = objects[0]['data']
            info = objects[0]['info']
            input_name = info[1]
            input_type_name = info[2].split('.')[1].split('-')[0]

        except Exception as e:
            raise ValueError('Unable to fetch input_ref object from workspace: ' + str(e))
            #to get the full stack trace: traceback.format_exc()

        if input_type_name == 'MSA':
            MSA_in = data
            row_order = []
            default_row_labels = dict()
            if 'row_order' in MSA_in.keys():
                row_order = MSA_in['row_order']
            else:
                row_order = sorted(MSA_in['alignment'].keys())

            if 'default_row_labels' in MSA_in.keys():
                default_row_labels = MSA_in['default_row_labels']
            else:
                for row_id in row_order:
                    default_row_labels[row_id] = row_id
            if len(row_order) < 2:
                self.log(invalid_msgs,"must have multiple records in MSA: "+params['input_ref'])

            # export features to FASTA file
            input_MSA_file_path = os.path.join(self.scratch, input_name+".fasta")
            self.log(console, 'writing fasta file: '+input_MSA_file_path)
            records = []
            for row_id in row_order:
                #self.log(console,"row_id: '"+row_id+"'")  # DEBUG
                #self.log(console,"alignment: '"+MSA_in['alignment'][row_id]+"'")  # DEBUG
            # using SeqIO makes multiline sequences.  (Gblocks doesn't care, but FastTree doesn't like multiline, and I don't care enough to change code)
                #record = SeqRecord(Seq(MSA_in['alignment'][row_id]), id=row_id, description=default_row_labels[row_id])
                #records.append(record)
            #SeqIO.write(records, input_MSA_file_path, "fasta")
                records.extend(['>'+row_id,
                                MSA_in['alignment'][row_id]
                               ])
            with open(input_MSA_file_path,'w',0) as input_MSA_file_handle:
                input_MSA_file_handle.write("\n".join(records)+"\n")


            # Determine whether nuc or protein sequences
            #
            NUC_MSA_pattern = re.compile("^[\.\-_ACGTUXNRYSWKMBDHVacgtuxnryswkmbdhv \t\n]+$")
            all_seqs_nuc = True
            for row_id in row_order:
                #self.log(console, row_id+": '"+MSA_in['alignment'][row_id]+"'")
                if NUC_MSA_pattern.match(MSA_in['alignment'][row_id]) == None:
                    all_seqs_nuc = False
                    break

        # Missing proper input_type
        #
        else:
            raise ValueError('Cannot yet handle input_ref type of: '+type_name)


        # DEBUG: check the MSA file contents
#        with open(input_MSA_file_path, 'r', 0) as input_MSA_file_handle:
#            for line in input_MSA_file_handle:
#                #self.log(console,"MSA_LINE: '"+line+"'")  # too big for console
#                self.log(invalid_msgs,"MSA_LINE: '"+line+"'")


        # validate input data
        #
        N_seqs = 0
        L_first_seq = 0
        with open(input_MSA_file_path, 'r', 0) as input_MSA_file_handle:
            for line in input_MSA_file_handle:
                if line.startswith('>'):
                    N_seqs += 1
                    continue
                if L_first_seq == 0:
                    for c in line:
                        if c != '-' and c != ' ' and c != "\n":
                            L_first_seq += 1
        # min_seqs_for_conserved
        if 'min_seqs_for_conserved' in params and params['min_seqs_for_conserved'] != None and int(params['min_seqs_for_conserved']) != 0:
            if int(params['min_seqs_for_conserved']) < int(0.5*N_seqs)+1:
                self.log(invalid_msgs,"Min Seqs for Conserved Pos ("+str(params['min_seqs_for_conserved'])+") must be >= N/2+1 (N="+str(N_seqs)+", N/2+1="+str(int(0.5*N_seqs)+1)+")\n")
            if int(params['min_seqs_for_conserved']) > int(params['min_seqs_for_flank']):
                self.log(invalid_msgs,"Min Seqs for Conserved Pos ("+str(params['min_seqs_for_conserved'])+") must be <= Min Seqs for Flank Pos ("+str(params['min_seqs_for_flank'])+")\n")

        # min_seqs_for_flank
        if 'min_seqs_for_flank' in params and params['min_seqs_for_flank'] != None and int(params['min_seqs_for_flank']) != 0:
            if int(params['min_seqs_for_flank']) > N_seqs:
                self.log(invalid_msgs,"Min Seqs for Flank Pos ("+str(params['min_seqs_for_flank'])+") must be <= N (N="+str(N_seqs)+")\n")

        # max_pos_contig_nonconserved
        if 'max_pos_contig_nonconserved' in params and params['max_pos_contig_nonconserved'] != None and int(params['max_pos_contig_nonconserved']) != 0:
            if int(params['max_pos_contig_nonconserved']) < 0:
                self.log(invalid_msgs,"Max Num Non-Conserved Pos ("+str(params['max_pos_contig_nonconserved'])+") must be >= 0"+"\n")
            if int(params['max_pos_contig_nonconserved']) > L_first_seq or int(params['max_pos_contig_nonconserved']) >= 32000:
                self.log(invalid_msgs,"Max Num Non-Conserved Pos ("+str(params['max_pos_contig_nonconserved'])+") must be <= L first seq ("+str(L_first_seq)+") and < 32000\n")

        # min_block_len
        if 'min_block_len' in params and params['min_block_len'] != None and int(params['min_block_len']) != 0:
            if int(params['min_block_len']) < 2:
                self.log(invalid_msgs,"Min Block Len ("+str(params['min_block_len'])+") must be >= 2"+"\n")
            if int(params['min_block_len']) > L_first_seq or int(params['min_block_len']) >= 32000:
                self.log(invalid_msgs,"Min Block Len ("+str(params['min_block_len'])+") must be <= L first seq ("+str(L_first_seq)+") and < 32000\n")

        # trim_level
        if 'trim_level' in params and params['trim_level'] != None and int(params['trim_level']) != 0:
            if int(params['trim_level']) < 0 or int(params['trim_level']) > 2:
                self.log(invalid_msgs,"Trim Level ("+str(params['trim_level'])+") must be >= 0 and <= 2"+"\n")


        if len(invalid_msgs) > 0:

            # load the method provenance from the context object
            self.log(console,"SETTING PROVENANCE")  # DEBUG
            provenance = [{}]
            if 'provenance' in ctx:
                provenance = ctx['provenance']
            # add additional info to provenance here, in this case the input data object reference
            provenance[0]['input_ws_objects'] = []
            provenance[0]['input_ws_objects'].append(params['input_ref'])
            provenance[0]['service'] = 'kb_gblocks'
            provenance[0]['method'] = 'run_Gblocks'

            # report
            report += "FAILURE\n\n"+"\n".join(invalid_msgs)+"\n"
            reportObj = {
                'objects_created':[],
                'text_message':report
                }

            reportName = 'gblocks_report_'+str(uuid.uuid4())
            report_obj_info = ws.save_objects({
#                'id':info[6],
                'workspace':params['workspace_name'],
                'objects':[
                    {
                        'type':'KBaseReport.Report',
                        'data':reportObj,
                        'name':reportName,
                        'meta':{},
                        'hidden':1,
                        'provenance':provenance
                    }
                ]
            })[0]


            self.log(console,"BUILDING RETURN OBJECT")
            returnVal = { 'report_name': reportName,
                          'report_ref': str(report_obj_info[6]) + '/' + str(report_obj_info[0]) + '/' + str(report_obj_info[4])
#                          'output_ref': None
                          }
            self.log(console,"run_Gblocks DONE")
            return [returnVal]


        ### Construct the command
        #
        #  e.g.
        #  for "0.5" gaps: cat "o\n<MSA_file>\nb\n5\ng\nm\nq\n" | Gblocks
        #  for "all" gaps: cat "o\n<MSA_file>\nb\n5\n5\ng\nm\nq\n" | Gblocks
        #
        gblocks_cmd = [self.GBLOCKS_bin]

        # check for necessary files
        if not os.path.isfile(self.GBLOCKS_bin):
            raise ValueError("no such file '"+self.GBLOCKS_bin+"'")
        if not os.path.isfile(input_MSA_file_path):
            raise ValueError("no such file '"+input_MSA_file_path+"'")
        if not os.path.getsize(input_MSA_file_path) > 0:
            raise ValueError("empty file '"+input_MSA_file_path+"'")

        # DEBUG
#        with open(input_MSA_file_path,'r',0) as input_MSA_file_handle:
#            for line in input_MSA_file_handle:
#                #self.log(console,"MSA LINE: '"+line+"'")  # too big for console
#                self.log(invalid_msgs,"MSA LINE: '"+line+"'")


        # set the output path
        timestamp = int((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds()*1000)
        output_dir = os.path.join(self.scratch,'output.'+str(timestamp))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Gblocks names output blocks MSA by appending "-gb" to input file
        #output_GBLOCKS_file_path = os.path.join(output_dir, input_name+'-gb')
        output_GBLOCKS_file_path = input_MSA_file_path+'-gb'
        output_aln_file_path = output_GBLOCKS_file_path

        # Gblocks is interactive and only accepts args from pipe input
        #if 'arg' in params and params['arg'] != None and params['arg'] != 0:
        #    fasttree_cmd.append('-arg')
        #    fasttree_cmd.append(val)


        # Run GBLOCKS, capture output as it happens
        #
        self.log(console, 'RUNNING GBLOCKS:')
        self.log(console, '    '+' '.join(gblocks_cmd))
#        report += "\n"+'running GBLOCKS:'+"\n"
#        report += '    '+' '.join(gblocks_cmd)+"\n"

        # FastTree requires shell=True in order to see input data
        env = os.environ.copy()
        #joined_fasttree_cmd = ' '.join(fasttree_cmd)  # redirect out doesn't work with subprocess unless you join command first
        #p = subprocess.Popen([joined_fasttree_cmd], \
        p = subprocess.Popen(gblocks_cmd, \
                             cwd = self.scratch, \
                             stdin = subprocess.PIPE, \
                             stdout = subprocess.PIPE, \
                             stderr = subprocess.PIPE, \
                             shell = True, \
                             env = env)
#                             executable = '/bin/bash' )

        
        # write commands to process
        #
        #  for "0.5" gaps: cat "o\n<MSA_file>\nb\n5\ng\nm\nq\n" | Gblocks
        #  for "all" gaps: cat "o\n<MSA_file>\nb\n5\n5\ng\nm\nq\n" | Gblocks

        p.stdin.write("o"+"\n")  # open MSA file
        p.stdin.write(input_MSA_file_path+"\n")

        if 'trim_level' in params and params['trim_level'] != None and int(params['trim_level']) != 0:
            p.stdin.write("b"+"\n")
            if int(params['trim_level']) >= 1:
                self.log (console,"changing trim level")
                p.stdin.write("5"+"\n")  # set to "half"
                if int(params['trim_level']) == 2:
                    self.log (console,"changing trim level")
                    p.stdin.write("5"+"\n")  # set to "all"
                elif int(params['trim_level']) > 2:
                    raise ValueError ("trim_level ("+str(params['trim_level'])+") was not between 0-2")
                p.stdin.write("m"+"\n")

        # flank must precede conserved because it acts us upper bound for acceptable conserved values
        if 'min_seqs_for_flank' in params and params['min_seqs_for_flank'] != None and int(params['min_seqs_for_flank']) != 0:
            self.log (console,"changing min_seqs_for_flank")
            p.stdin.write("b"+"\n")
            p.stdin.write("2"+"\n")
            p.stdin.write(str(params['min_seqs_for_flank'])+"\n")
            p.stdin.write("m"+"\n")

        if 'min_seqs_for_conserved' in params and params['min_seqs_for_conserved'] != None and int(params['min_seqs_for_conserved']) != 0:
            self.log (console,"changing min_seqs_for_conserved")
            p.stdin.write("b"+"\n")
            p.stdin.write("1"+"\n")
            p.stdin.write(str(params['min_seqs_for_conserved'])+"\n")
            p.stdin.write("m"+"\n")

        if 'max_pos_contig_nonconserved' in params and params['max_pos_contig_nonconserved'] != None and int(params['max_pos_contig_nonconserved']) > -1:
            self.log (console,"changing max_pos_contig_nonconserved")
            p.stdin.write("b"+"\n")
            p.stdin.write("3"+"\n")
            p.stdin.write(str(params['max_pos_contig_nonconserved'])+"\n")
            p.stdin.write("m"+"\n")

        if 'min_block_len' in params and params['min_block_len'] != None and params['min_block_len'] != 0:
            self.log (console,"changing min_block_len")
            p.stdin.write("b"+"\n")
            p.stdin.write("4"+"\n")
            p.stdin.write(str(params['min_block_len'])+"\n")
            p.stdin.write("m"+"\n")
        
        p.stdin.write("g"+"\n")  # get blocks
        p.stdin.write("q"+"\n")  # quit
        p.stdin.close()
        p.wait()


        # Read output
        #
        while True:
            line = p.stdout.readline()
            #line = p.stderr.readline()
            if not line: break
            self.log(console, line.replace('\n', ''))

        p.stdout.close()
        #p.stderr.close()
        p.wait()
        self.log(console, 'return code: ' + str(p.returncode))
#        if p.returncode != 0:
        if p.returncode != 1:
            raise ValueError('Error running GBLOCKS, return code: '+str(p.returncode) + 
                '\n\n'+ '\n'.join(console))

        # Check that GBLOCKS produced output
        #
        if not os.path.isfile(output_GBLOCKS_file_path):
            raise ValueError("failed to create GBLOCKS output: "+output_GBLOCKS_file_path)
        elif not os.path.getsize(output_GBLOCKS_file_path) > 0:
            raise ValueError("created empty file for GBLOCKS output: "+output_GBLOCKS_file_path)


        # load the method provenance from the context object
        #
        self.log(console,"SETTING PROVENANCE")  # DEBUG
        provenance = [{}]
        if 'provenance' in ctx:
            provenance = ctx['provenance']
        # add additional info to provenance here, in this case the input data object reference
        provenance[0]['input_ws_objects'] = []
        provenance[0]['input_ws_objects'].append(params['input_ref'])
        provenance[0]['service'] = 'kb_gblocks'
        provenance[0]['method'] = 'run_Gblocks'


        # reformat output to single-line FASTA MSA and check that output not empty (often happens when param combinations don't produce viable blocks
        #
        output_fasta_buf = []
        id_order = []
        this_id = None
        ids = dict()
        alignment = dict()
        L_alignment = 0;
        L_alignment_set = False
        with open(output_GBLOCKS_file_path,'r',0) as output_GBLOCKS_file_handle:
            for line in output_GBLOCKS_file_handle:
                line = line.rstrip()
                if line.startswith('>'):
                    this_id = line[1:]
                    output_fasta_buf.append ('>'+re.sub('\s','_',default_row_labels[this_id]))
                    id_order.append(this_id)
                    alignment[this_id] = ''
                    if L_alignment != 0 and not L_alignment_set:
                         L_alignment_set = True
                    continue
                output_fasta_buf.append (line)
                for c in line:
                    if c != ' ' and c != "\n":
                        alignment[this_id] += c
                        if not L_alignment_set:
                            L_alignment += 1
        if L_alignment == 0:
            self.log(invalid_msgs,"params produced no blocks.  Consider changing to less stringent values")
        else:
            if 'remove_mask_positions_flag' in params and params['remove_mask_positions_flag'] != None and int(params['remove_mask_positions_flag']) != 0:
                self.log (console,"removing mask positions")
                mask = []
                new_alignment = dict()
                for i in range(0,L_alignment):
                    mask[i] = '+'
                    if alignment[id_order[0]][i] == '-' \
                        or alignment[id_order[0]][i] == 'X' \
                        or alignment[id_order[0]][i] == 'x':
                        mask[i] = '-'
                for row_id in id_order:
                    new_alignment[row_id] = ''
                    for i,c in enumerate(alignment[row_id]):
                         if mask[i] == '+':
                            new_alignment[row_id] += c
                alignment = new_alignment

            L_alignment = len(alignment[id_order[0]])

            # write fasta with tidied ids
            output_MSA_file_path = os.path.join(output_dir, params['output_name']+'.fasta');
            with open(output_MSA_file_path,'w',0) as output_MSA_file_handle:
                output_MSA_file_handle.write("\n".join(output_fasta_buf)+"\n")


        # Upload results
        #
        if len(invalid_msgs) == 0:
            self.log(console,"UPLOADING RESULTS")  # DEBUG

# Didn't write file
#            with open(output_MSA_file_path,'r',0) as output_MSA_file_handle:
#                output_MSA_buf = output_MSA_file_handle.read()
#            output_MSA_buf = output_MSA_buf.rstrip()
#            self.log(console,"\nMSA:\n"+output_MSA_buf+"\n")
        
            # Build output_MSA structure
            #   first extract old info from MSA (labels, ws_refs, etc.)
            #
            MSA_out = dict()
            for key in MSA_in.keys():
                 MSA_out[key] = MSA_in[key]

            # then replace with new info
            #
            MSA_out['alignment'] = alignment
            MSA_out['name'] = params['output_name']
            MSA_out['alignment_length'] = alignment_length = L_alignment
            MSA_name = params['output_name']
            MSA_description = ''
            if 'desc' in params and params['desc'] != None and params['desc'] != '':
                MSA_out['desc'] = MSA_description = params['desc']

            # Store MSA_out
            #
            new_obj_info = ws.save_objects({
                            'workspace': params['workspace_name'],
                            'objects':[{
                                    'type': 'KBaseTrees.MSA',
                                    'data': MSA_out,
                                    'name': params['output_name'],
                                    'meta': {},
                                    'provenance': provenance
                                }]
                        })[0]


            # create CLW formatted output file
            max_row_width = 60
            id_aln_gap_width = 1
            gap_chars = ''
            for sp_i in range(id_aln_gap_width):
                gap_chars += ' '
            # DNA
            if all_seqs_nuc:
                strong_groups = { 'AG': True,
                                  'CTU': True
                                  }
                weak_groups = None
            # PROTEINS
            else:
                strong_groups = { 'AST':  True,
                                  'EKNQ': True,
                                  'HKNQ': True,
                                  'DENQ': True,
                                  'HKQR': True,
                                  'ILMV': True,
                                  'FILM': True,
                                  'HY':   True,
                                  'FWY':  True
                                  }
                weak_groups = { 'ACS':    True,
                                'ATV':    True,
                                'AGS':    True,
                                'KNST':   True,
                                'APST':   True,
                                'DGNS':   True,
                                'DEKNQS': True,
                                'DEHKNQ': True,
                                'EHKNQR': True,
                                'FILMV':  True,
                                'FHY':    True
                                }
                
            clw_buf = []
            clw_buf.append ('CLUSTALW format of GBLOCKS trimmed MSA '+MSA_name+': '+MSA_description)
            clw_buf.append ('')

            long_id_len = 0
            aln_pos_by_id = dict()
            for row_id in row_order:
                aln_pos_by_id[row_id] = 0
                row_id_disp = default_row_labels[row_id]
                if long_id_len < len(row_id_disp):
                    long_id_len = len(row_id_disp)

            full_row_cnt = alignment_length // max_row_width
            if alignment_length % max_row_width == 0:
                full_row_cnt -= 1
            for chunk_i in range (full_row_cnt + 1):
                for row_id in row_order:
                    row_id_disp = re.sub('\s','_',default_row_labels[row_id])
                    for sp_i in range (long_id_len-len(row_id_disp)):
                        row_id_disp += ' '

                    aln_chunk_upper_bound = (chunk_i+1)*max_row_width
                    if aln_chunk_upper_bound > alignment_length:
                        aln_chunk_upper_bound = alignment_length
                    aln_chunk = alignment[row_id][chunk_i*max_row_width:aln_chunk_upper_bound]
                    for c in aln_chunk:
                        if c != '-':
                            aln_pos_by_id[row_id] += 1

                    clw_buf.append (row_id_disp+gap_chars+aln_chunk+' '+str(aln_pos_by_id[row_id]))

                # conservation line
                cons_line = ''
                for pos_i in range(chunk_i*max_row_width, aln_chunk_upper_bound):
                    col_chars = dict()
                    seq_cnt = 0
                    for row_id in row_order:
                        char = alignment[row_id][pos_i]
                        if char != '-':
                            seq_cnt += 1
                            col_chars[char] = True
                    if seq_cnt <= 1:
                        cons_char = ' '
                    elif len(col_chars.keys()) == 1:
                        cons_char = '*'
                    else:
                        strong = False
                        for strong_group in strong_groups.keys():
                            this_strong_group = True
                            for seen_char in col_chars.keys():
                                if seen_char not in strong_group:
                                    this_strong_group = False
                                    break
                            if this_strong_group:
                                strong = True
                                break
                        if not strong:
                            weak = False
                            if weak_groups != None:
                                for weak_group in weak_groups.keys():
                                    this_weak_group = True
                                    for seen_char in col_chars.keys():
                                        if seen_char not in weak_group:
                                            this_strong_group = False
                                            break
                                    if this_weak_group:
                                        weak = True
                        if strong:
                            cons_char = ':'
                        elif weak:
                            cons_char = '.'
                        else:
                            cons_char = ' '
                    cons_line += cons_char

                lead_space = ''
                for sp_i in range(long_id_len):
                    lead_space += ' '
                lead_space += gap_chars

                clw_buf.append(lead_space+cons_line)
                clw_buf.append('')

            # write clw to file
            clw_buf_str = "\n".join(clw_buf)+"\n"
            output_clw_file_path = os.path.join(output_dir, input_name+'-MSA.clw');
            with open (output_clw_file_path, "w", 0) as output_clw_file_handle:
                output_clw_file_handle.write(clw_buf_str)
            output_clw_file_handle.close()


            # upload GBLOCKS FASTA output to SHOCK for file_links
            dfu = DFUClient(self.callbackURL)
            try:
                output_upload_ret = dfu.file_to_shock({'file_path': output_aln_file_path,
# DEBUG
#                                                      'make_handle': 0,
#                                                      'pack': 'zip'})
                                                       'make_handle': 0})
            except:
                raise ValueError ('error loading aln_out file to shock')

            # upload GBLOCKS CLW output to SHOCK for file_links
            try:
                output_clw_upload_ret = dfu.file_to_shock({'file_path': output_clw_file_path,
# DEBUG
#                                                      'make_handle': 0,
#                                                      'pack': 'zip'})
                                                           'make_handle': 0})
            except:
                raise ValueError ('error loading clw_out file to shock')


            # make HTML reports
            #
            # HERE


            # build output report object
            #
            self.log(console,"BUILDING REPORT")  # DEBUG

            reportName = 'gblocks_report_'+str(uuid.uuid4())
            reportObj = {
                'objects_created':[{'ref':params['workspace_name']+'/'+params['output_name'],
                                    'description':'GBLOCKS MSA'}],
                #'message': '',
                'message': clw_buf_str,
                'direct_html': '',
                'direct_html_index': None,
                'file_links': [],
                'html_links': [],
                'workspace_name': params['workspace_name'],
                'report_object_name': reportName
                }
            reportObj['file_links'] = [{'shock_id': output_upload_ret['shock_id'],
                                        'name': params['output_name']+'-GBLOCKS.FASTA',
                                        'label': 'GBLOCKS-trimmed MSA FASTA'
                                        },
                                       {'shock_id': output_clw_upload_ret['shock_id'],
                                        'name': params['output_name']+'-GBLOCKS.CLW',
                                        'label': 'GBLOCKS-trimmed MSA CLUSTALW'
                                        }]

            # save report object
            #
            SERVICE_VER = 'release'
            reportClient = KBaseReport(self.callbackURL, token=ctx['token'], service_ver=SERVICE_VER)
            #report_info = report.create({'report':reportObj, 'workspace_name':params['workspace_name']})
            report_info = reportClient.create_extended_report(reportObj)                                       

        else:  # len(invalid_msgs) > 0
            reportName = 'gblocks_report_'+str(uuid.uuid4())
            report += "FAILURE:\n\n"+"\n".join(invalid_msgs)+"\n"
            reportObj = {
                'objects_created':[],
                'text_message':report
                }

            ws = workspaceService(self.workspaceURL, token=ctx['token'])
            report_obj_info = ws.save_objects({
                    #'id':info[6],
                    'workspace':params['workspace_name'],
                    'objects':[
                        {
                            'type':'KBaseReport.Report',
                            'data':reportObj,
                            'name':reportName,
                            'meta':{},
                            'hidden':1,
                            'provenance':provenance
                            }
                        ]
                    })[0]

            report_info = dict()
            report_info['name'] = report_obj_info[1]
            report_info['ref'] = str(report_obj_info[6])+'/'+str(report_obj_info[0])+'/'+str(report_obj_info[4])


        # done
        returnVal = { 'report_name': report_info['name'],
                      'report_ref': report_info['ref']
                      }

        self.log(console,"run_Gblocks DONE")
        #END run_Gblocks

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError('Method run_Gblocks return value ' +
                             'returnVal is not type dict as required.')
        # return the results
        return [returnVal]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
