
using Newtonsoft.Json;
using Newtonsoft.Json.Converters;
using System.Runtime.Serialization;

namespace Co3.Rest.Dto
{
    [DataContract]
    [JsonConverter(typeof(StringEnumConverter))]
    public enum GeoType
    {
        [EnumMember(Value = "city")]
        City,

        [EnumMember(Value = "state")]
        State,

        [EnumMember(Value = "province")]
        Province,

        [EnumMember(Value = "country")]
        Country,

        [EnumMember(Value = "metacountry")]
        MetaCountry
    }
}
