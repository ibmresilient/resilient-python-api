using Newtonsoft.Json;
using Newtonsoft.Json.Converters;
using System.Runtime.Serialization;

namespace Co3.Rest.Dto
{
    [JsonConverter(typeof(StringEnumConverter))]
    public enum ThreatSourceTosElementType
    {
        [EnumMember(Value = "url")]
        Url,
        [EnumMember(Value = "test")]
        Text,
        [EnumMember(Value = "check")]
        Check
    }
}
