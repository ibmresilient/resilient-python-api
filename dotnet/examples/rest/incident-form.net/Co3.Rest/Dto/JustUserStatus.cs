
using Newtonsoft.Json;
using Newtonsoft.Json.Converters;
using System.Runtime.Serialization;

namespace Co3.Rest.Dto
{
    [DataContract]
    [JsonConverter(typeof(StringEnumConverter))]
    public enum JustUserStatus
    {
        /// <summary>
        /// The user is active
        /// </summary>
        [EnumMember(Value = "A")]
        Active,

        /// <summary>
        /// The user is deactivated
        /// </summary>
        [EnumMember(Value = "D")]
        Deactivated,

        /// <summary>
        /// The user is inactive
        /// </summary>
        [EnumMember(Value = "I")]
        Inactive,

        /// <summary>
        /// The user is pending activation (i.e. an invitation was created but not accepted by the user).
        /// </summary>
        [EnumMember(Value = "P")]
        PendingActivation,

        /// <summary>
        /// The user is being reset
        /// </summary>
        [EnumMember(Value = "R")]
        Reset,

        /// <summary>
        /// The user is unknown (used for external users)
        /// </summary>
        [EnumMember(Value = "U")]
        Unknown
    }
}
