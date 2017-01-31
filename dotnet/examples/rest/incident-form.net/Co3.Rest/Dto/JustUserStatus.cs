
using Newtonsoft.Json;
using Newtonsoft.Json.Converters;
using System.Runtime.Serialization;

namespace Co3.Rest.Dto
{
    [DataContract]
    [JsonConverter(typeof(StringEnumConverter))]
    public enum JustUserStatus
    {
        [EnumMember(Value = "A")]
        Active,

        [EnumMember(Value = "I")]
        Inactive,

        [EnumMember(Value = "P")]
        PendingActivation,

        [EnumMember(Value = "R")]
        Reset
    }
}
