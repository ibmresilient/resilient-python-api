
using Newtonsoft.Json;
using Newtonsoft.Json.Converters;
using System.Runtime.Serialization;

namespace Co3.Rest.Dto
{
    [JsonConverter(typeof(StringEnumConverter))]
    public enum TextFormat
    {
        [EnumMember(Value = "text")]
        Text,
        [EnumMember(Value = "html")]
        Html,
        [EnumMember(Value = "unknown")]
        Unknown
    }
}
