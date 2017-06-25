
package us.kbase.kbgblocks;

import java.util.HashMap;
import java.util.Map;
import javax.annotation.Generated;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


/**
 * <p>Original spec-file type: Gblocks_Params</p>
 * <pre>
 * Gblocks Input Params
 * </pre>
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "workspace_name",
    "desc",
    "input_ref",
    "output_name",
    "trim_level",
    "min_seqs_for_conserved",
    "min_seqs_for_flank",
    "max_pos_contig_nonconserved",
    "min_block_len",
    "remove_mask_positions_flag"
})
public class GblocksParams {

    @JsonProperty("workspace_name")
    private String workspaceName;
    @JsonProperty("desc")
    private String desc;
    @JsonProperty("input_ref")
    private String inputRef;
    @JsonProperty("output_name")
    private String outputName;
    @JsonProperty("trim_level")
    private Long trimLevel;
    @JsonProperty("min_seqs_for_conserved")
    private Long minSeqsForConserved;
    @JsonProperty("min_seqs_for_flank")
    private Long minSeqsForFlank;
    @JsonProperty("max_pos_contig_nonconserved")
    private Long maxPosContigNonconserved;
    @JsonProperty("min_block_len")
    private Long minBlockLen;
    @JsonProperty("remove_mask_positions_flag")
    private Long removeMaskPositionsFlag;
    private Map<String, Object> additionalProperties = new HashMap<String, Object>();

    @JsonProperty("workspace_name")
    public String getWorkspaceName() {
        return workspaceName;
    }

    @JsonProperty("workspace_name")
    public void setWorkspaceName(String workspaceName) {
        this.workspaceName = workspaceName;
    }

    public GblocksParams withWorkspaceName(String workspaceName) {
        this.workspaceName = workspaceName;
        return this;
    }

    @JsonProperty("desc")
    public String getDesc() {
        return desc;
    }

    @JsonProperty("desc")
    public void setDesc(String desc) {
        this.desc = desc;
    }

    public GblocksParams withDesc(String desc) {
        this.desc = desc;
        return this;
    }

    @JsonProperty("input_ref")
    public String getInputRef() {
        return inputRef;
    }

    @JsonProperty("input_ref")
    public void setInputRef(String inputRef) {
        this.inputRef = inputRef;
    }

    public GblocksParams withInputRef(String inputRef) {
        this.inputRef = inputRef;
        return this;
    }

    @JsonProperty("output_name")
    public String getOutputName() {
        return outputName;
    }

    @JsonProperty("output_name")
    public void setOutputName(String outputName) {
        this.outputName = outputName;
    }

    public GblocksParams withOutputName(String outputName) {
        this.outputName = outputName;
        return this;
    }

    @JsonProperty("trim_level")
    public Long getTrimLevel() {
        return trimLevel;
    }

    @JsonProperty("trim_level")
    public void setTrimLevel(Long trimLevel) {
        this.trimLevel = trimLevel;
    }

    public GblocksParams withTrimLevel(Long trimLevel) {
        this.trimLevel = trimLevel;
        return this;
    }

    @JsonProperty("min_seqs_for_conserved")
    public Long getMinSeqsForConserved() {
        return minSeqsForConserved;
    }

    @JsonProperty("min_seqs_for_conserved")
    public void setMinSeqsForConserved(Long minSeqsForConserved) {
        this.minSeqsForConserved = minSeqsForConserved;
    }

    public GblocksParams withMinSeqsForConserved(Long minSeqsForConserved) {
        this.minSeqsForConserved = minSeqsForConserved;
        return this;
    }

    @JsonProperty("min_seqs_for_flank")
    public Long getMinSeqsForFlank() {
        return minSeqsForFlank;
    }

    @JsonProperty("min_seqs_for_flank")
    public void setMinSeqsForFlank(Long minSeqsForFlank) {
        this.minSeqsForFlank = minSeqsForFlank;
    }

    public GblocksParams withMinSeqsForFlank(Long minSeqsForFlank) {
        this.minSeqsForFlank = minSeqsForFlank;
        return this;
    }

    @JsonProperty("max_pos_contig_nonconserved")
    public Long getMaxPosContigNonconserved() {
        return maxPosContigNonconserved;
    }

    @JsonProperty("max_pos_contig_nonconserved")
    public void setMaxPosContigNonconserved(Long maxPosContigNonconserved) {
        this.maxPosContigNonconserved = maxPosContigNonconserved;
    }

    public GblocksParams withMaxPosContigNonconserved(Long maxPosContigNonconserved) {
        this.maxPosContigNonconserved = maxPosContigNonconserved;
        return this;
    }

    @JsonProperty("min_block_len")
    public Long getMinBlockLen() {
        return minBlockLen;
    }

    @JsonProperty("min_block_len")
    public void setMinBlockLen(Long minBlockLen) {
        this.minBlockLen = minBlockLen;
    }

    public GblocksParams withMinBlockLen(Long minBlockLen) {
        this.minBlockLen = minBlockLen;
        return this;
    }

    @JsonProperty("remove_mask_positions_flag")
    public Long getRemoveMaskPositionsFlag() {
        return removeMaskPositionsFlag;
    }

    @JsonProperty("remove_mask_positions_flag")
    public void setRemoveMaskPositionsFlag(Long removeMaskPositionsFlag) {
        this.removeMaskPositionsFlag = removeMaskPositionsFlag;
    }

    public GblocksParams withRemoveMaskPositionsFlag(Long removeMaskPositionsFlag) {
        this.removeMaskPositionsFlag = removeMaskPositionsFlag;
        return this;
    }

    @JsonAnyGetter
    public Map<String, Object> getAdditionalProperties() {
        return this.additionalProperties;
    }

    @JsonAnySetter
    public void setAdditionalProperties(String name, Object value) {
        this.additionalProperties.put(name, value);
    }

    @Override
    public String toString() {
        return ((((((((((((((((((((((("GblocksParams"+" [workspaceName=")+ workspaceName)+", desc=")+ desc)+", inputRef=")+ inputRef)+", outputName=")+ outputName)+", trimLevel=")+ trimLevel)+", minSeqsForConserved=")+ minSeqsForConserved)+", minSeqsForFlank=")+ minSeqsForFlank)+", maxPosContigNonconserved=")+ maxPosContigNonconserved)+", minBlockLen=")+ minBlockLen)+", removeMaskPositionsFlag=")+ removeMaskPositionsFlag)+", additionalProperties=")+ additionalProperties)+"]");
    }

}
