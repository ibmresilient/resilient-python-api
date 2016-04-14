/*
 * Resilient Systems, Inc. ("Resilient") is willing to license software
 * or access to software to the company or entity that will be using or
 * accessing the software and documentation and that you represent as
 * an employee or authorized agent ("you" or "your") only on the condition
 * that you accept all of the terms of this license agreement.
 *
 * The software and documentation within Resilient's Development Kit are
 * copyrighted by and contain confidential information of Resilient. By
 * accessing and/or using this software and documentation, you agree that
 * while you may make derivative works of them, you:
 *
 * 1)  will not use the software and documentation or any derivative
 *     works for anything but your internal business purposes in
 *     conjunction your licensed used of Resilient's software, nor
 * 2)  provide or disclose the software and documentation or any
 *     derivative works to any third party.
 *
 * THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL RESILIENT BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.Serialization;
using Co3.Rest.JsonConverters;
using Newtonsoft.Json;
using Newtonsoft.Json.Converters;

namespace Co3.Rest.Dto
{
    [DataContract]
    [JsonConverter(typeof(StringEnumConverter))]
    public enum InputType
    {
        [EnumMember(Value = "boolean")]
        Boolean,

        [EnumMember(Value = "datepicker")]
        DatePicker,

        [EnumMember(Value = "multiselect")]
        MultiSelect,

        [EnumMember(Value = "select")]
        Select,

        [EnumMember(Value = "text")]
        Text,

        [EnumMember(Value = "textarea")]
        TextArea,

        [EnumMember(Value = "number")]
        Number,

        [EnumMember(Value = "multiselect_incident")]
        MultiSelectIncident,

        [EnumMember(Value = "multiselect_task")]
        MultiSelectTask,

        [EnumMember(Value = "select_owner")]
        SelectOwner,

        [EnumMember(Value = "multiselect_members")]
        MultiSelectMembers,

        [EnumMember(Value = "datetimepicker")]
        DateTimePicker,

        [EnumMember(Value = "select_user")]
        SelectUser,

        [EnumMember(Value = "none")]
        None
    }

    [DataContract]
    [JsonConverter(typeof(StringEnumConverter))]
    public enum FieldRequired
    {
        [JsonIgnore]
        Optional,

        [EnumMember(Value = "ALWAYS")]
        Always,

        [EnumMember(Value = "CLOSE")]
        Close
    }

    [DataContract]
    [JsonConverter(typeof(StringEnumConverter))]
    public enum MethodName
    {
        [EnumMember(Value = "CHANGED")]
        Changed,

        [EnumMember(Value = "EQUALS")]
        Equals,

        [EnumMember(Value = "CHANGED_TO")]
        ChangedTo,

        [EnumMember(Value = "CHANGED_FROM")]
        ChangedFrom,

        [EnumMember(Value = "OBJECT_REMOVED")]
        ObjectRemoved,

        [EnumMember(Value = "OBJECT_ADDED")]
        ObjectAdded,

        [EnumMember(Value = "VALUE_ADDED")]
        ValueAdded,

        [EnumMember(Value = "CONTAINS")]
        Contains,

        [EnumMember(Value = "DUE_WITHIN")]
        DueWithin,

        [EnumMember(Value = "OVERDUE_BY")]
        OverdueBy,

        [EnumMember(Value = "GT")]
        Gt,

        [EnumMember(Value = "LT")]
        Lt,

        [EnumMember(Value = "GTE")]
        Gte,

        [EnumMember(Value = "LTE")]
        Lte,

        [EnumMember(Value = "CONTAINS_USER")]
        ContainsUser,

        [EnumMember(Value = "IN")]
        In,

        [EnumMember(Value = "VALUE_REMOVED")]
        ValueRemoved
    }

    public class FieldDefDto : PartialFieldDefDto
    {
        [JsonProperty("type_id")]
        public int TypeId { get; set; }

        [JsonProperty("tooltip")]
        public string Tooltip { get; set; }

        [JsonProperty("placeholder")]
        public string Placeholder { get; set; }

        [JsonProperty("input_type")]
        public InputType InputType { get; set; }

        [JsonProperty("required")]
        [DefaultValue(FieldRequired.Optional)]
        public FieldRequired Required { get; set; }

        [JsonProperty("hide_notification")]
        public bool HideNotification { get; set; }

        [JsonProperty("chosen")]
        public bool Chosen { get; set; }

        [JsonProperty("blank_option")]
        public bool BlankOption { get; set; }

        [JsonProperty("internal")]
        public bool Internal { get; set; }

        [JsonProperty("operations")]
        public List<MethodName> Operations { get; set; }

        [JsonProperty("values")]
        public List<FieldDefValueDto> Values { get; set; }

        [JsonProperty("uuid")]
        public Guid Uuid { get; set; }

        [JsonProperty("perms")]
        public FieldDefPermsDto Perms { get; set; }

        [JsonProperty("read_only")]
        public bool ReadOnly { get; set; }

        [JsonProperty("operation_perms")]
        public Dictionary<string, MethodNamePermsDto> OperationPerms { get; set; }

        [JsonProperty("changeable")]
        public bool Changeable { get; set; }

        [JsonProperty("label_false")]
        public string LabelFalse { get; set; }

        [JsonProperty("label_true")]
        public string LabelTrue { get; set; }

        [JsonProperty("rich_text")]
        public bool RichText { get; set; }

        [JsonProperty("export_key")]
        public string ExportKey { get; set; }

        [JsonProperty("order")]
        public int Order { get; set; }

        [JsonProperty("width")]
        public int Width { get; set; }

        public override string ToString()
        {
            return Text;
        }
    }
}
