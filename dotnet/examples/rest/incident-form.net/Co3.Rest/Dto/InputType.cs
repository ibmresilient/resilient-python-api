
using Newtonsoft.Json;
using Newtonsoft.Json.Converters;
using System.Runtime.Serialization;

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
}
