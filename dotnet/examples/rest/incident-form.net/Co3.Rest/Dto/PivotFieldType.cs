using System.Runtime.Serialization;

namespace Co3.Rest.Dto
{
    public enum PivotFieldType
    {
        [EnumMember(Value = "field")]
        Field,
        [EnumMember(Value = "number_difference")]
        NumberDifference,
        [EnumMember(Value = "date_difference")]
        DateDifference
    }
}
