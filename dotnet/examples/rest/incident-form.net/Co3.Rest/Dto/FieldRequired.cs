using Newtonsoft.Json;
using Newtonsoft.Json.Converters;
using System.Runtime.Serialization;

namespace Co3.Rest.Dto
{
    [DataContract]
    [JsonConverter(typeof(StringEnumConverter))]
    public enum FieldRequired
    {
        [JsonIgnore]
        Optional,

        [EnumMember(Value = "always")]
        Always,

        [EnumMember(Value = "close")]
        Close
    }
}
