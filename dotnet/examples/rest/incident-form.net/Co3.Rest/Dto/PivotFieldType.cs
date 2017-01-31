using System.Runtime.Serialization;
using Newtonsoft.Json;
using Newtonsoft.Json.Converters;

namespace Co3.Rest.Dto
{
    [JsonConverter(typeof(StringEnumConverter))]
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
