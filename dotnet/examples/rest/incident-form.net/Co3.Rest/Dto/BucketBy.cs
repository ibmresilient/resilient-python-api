
using System.Runtime.Serialization;

namespace Co3.Rest.Dto
{
    public enum BucketBy
    {
        [EnumMember(Value = "minute")]
        Minute,
        [EnumMember(Value = "hour")]
        Hour,
        [EnumMember(Value = "day")]
        Day,
        [EnumMember(Value = "week")]
        Week,
        [EnumMember(Value = "month")]
        Month,
        [EnumMember(Value = "year")]
        Year,
        [EnumMember(Value = "default_resolution")]
        DefaultResolution,
        [EnumMember(Value = "minute_resolution")]
        MinuteResolution
    }
}
