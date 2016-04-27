/*
** A KBase module: gblocks
**
** This module runs Gblocks trim Multiple Sequence Alignments (MSAs) to remove hypervariable (gappy) regions using Gblocks
** 
*/

module kb_gblocks {

    /* 
    ** The workspace object refs are of form:
    **
    **    objects = ws.get_objects([{'ref': params['workspace_id']+'/'+params['obj_name']}])
    **
    ** "ref" means the entire name combining the workspace id and the object name
    ** "id" is a numerical identifier of the workspace or object, and should just be used for workspace
    ** "name" is a string identifier of a workspace or object.  This is received from Narrative.
    */
    typedef string workspace_name;
    typedef string data_obj_name;
    typedef string data_obj_ref;


    /* Gblocks Input Params
    */
    typedef structure {
        workspace_name workspace_name;
	string         desc;
	data_obj_name  input_name;
	data_obj_name  input_mask_name;
        data_obj_name  output_name;
	int            trim_level;
    } Gblocks_Params;


    /* Gblocks Output
    */
    typedef structure {
	data_obj_name report_name;
	data_obj_ref  report_ref;
        data_obj_ref  output_ref;
    } Gblocks_Output;
	

    /*  Method for trimming MSAs of either DNA or PROTEIN sequences
    **
    **        input_type: MSA
    **        output_type: MSA
    */
    funcdef run_Gblocks (Gblocks_Params params)  returns (Gblocks_Output) authentication required;
};
