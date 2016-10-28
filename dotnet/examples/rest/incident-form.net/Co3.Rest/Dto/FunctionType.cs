using Newtonsoft.Json;
using Newtonsoft.Json.Converters;
using System.Runtime.Serialization;

namespace Co3.Rest.Dto
{
    [JsonConverter(typeof(StringEnumConverter))]
    public enum FunctionType
    {
        [EnumMember(Value = "count")]
        Count,
        [EnumMember(Value = "average")]
        Average
    }
}
