using Newtonsoft.Json;
using Newtonsoft.Json.Converters;
using System.Runtime.Serialization;

namespace Co3.Rest.Dto
{
    [JsonConverter(typeof(StringEnumConverter))]
    public enum PropertyTypes
    {
        [EnumMember(Value = "string")]
        String,
        [EnumMember(Value = "number")]
        Number,
        [EnumMember(Value = "uri")]
        Uri,
        [EnumMember(Value = "ip")]
        Ip,
        [EnumMember(Value = "lat_lng")]
        LatLng
    }
}
