using Newtonsoft.Json;
using Newtonsoft.Json.Converters;
using System.Runtime.Serialization;

namespace Co3.Rest.Dto
{
    [JsonConverter(typeof(StringEnumConverter))]
    public enum OperationType
    {
        [EnumMember(Value = "created")]
        Created,
        [EnumMember(Value = "deleted")]
        Deleted,
        [EnumMember(Value = "modified")]
        Modified
    }
}
