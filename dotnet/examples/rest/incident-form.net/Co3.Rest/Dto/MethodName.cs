using Newtonsoft.Json;
using Newtonsoft.Json.Converters;
using System.Runtime.Serialization;

namespace Co3.Rest.Dto
{
    [DataContract]
    [JsonConverter(typeof(StringEnumConverter))]
    public enum MethodName
    {
        [EnumMember(Value = "changed")]
        Changed,

        [EnumMember(Value = "equals")]
        Equals,

        [EnumMember(Value = "changed_to")]
        ChangedTo,

        [EnumMember(Value = "changed_from")]
        ChangedFrom,

        [EnumMember(Value = "object_removed")]
        ObjectRemoved,

        [EnumMember(Value = "object_added")]
        ObjectAdded,

        [EnumMember(Value = "value_added")]
        ValueAdded,

        [EnumMember(Value = "contains")]
        Contains,

        [EnumMember(Value = "due_within")]
        DueWithin,

        [EnumMember(Value = "overdue_by")]
        OverdueBy,

        [EnumMember(Value = "gt")]
        Gt,

        [EnumMember(Value = "lt")]
        Lt,

        [EnumMember(Value = "gte")]
        Gte,

        [EnumMember(Value = "lte")]
        Lte,

        [EnumMember(Value = "contains_user")]
        ContainsUser,

        [EnumMember(Value = "in")]
        In,

        [EnumMember(Value = "value_removed")]
        ValueRemoved,

        [EnumMember(Value = "not_in")]
        NotIn,

        [EnumMember(Value = "not_equals")]
        NotEquals,

        [EnumMember(Value = "not_contains")]
        NotContains,

        [EnumMember(Value = "not_contains_user")]
        NotContainsUser,

        [EnumMember(Value = "not_changed_to")]
        NotChangedTo,

        [EnumMember(Value = "not_changed_from")]
        NotChangedFrom,

        [EnumMember(Value = "has_a_value")]
        HasAValue,

        [EnumMember(Value = "not_has_a_value")]
        NotHasAValue,
    }

}
