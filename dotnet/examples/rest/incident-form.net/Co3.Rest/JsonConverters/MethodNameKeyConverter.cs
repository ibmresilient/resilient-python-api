using System;
using System.Collections.Generic;
using System.Linq;
using Co3.Rest.Dto;
using Co3.Rest.Util;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Co3.Rest.JsonConverters
{
    public class MethodNameKeyConverter<T> : JsonConverter
    {
        public override bool CanConvert(Type objectType)
        {
            return objectType.IsAssignableFrom(typeof(Dictionary<MethodName, T>));
        }

        public override object ReadJson(JsonReader reader, Type objectType, object existingValue, JsonSerializer serializer)
        {
            Type type = typeof(MethodName);
            Dictionary<MethodName, T> returnValues = (Dictionary<MethodName, T>)Activator.CreateInstance(objectType);
            foreach (KeyValuePair<string, T> keyVaule in serializer.Deserialize<Dictionary<string, T>>(reader))
            {
                returnValues.Add((MethodName)EnumUtil.GetEnumFromJsonName(type, keyVaule.Key), keyVaule.Value);
            }

            return returnValues;
        }

        public override void WriteJson(JsonWriter writer, object value, JsonSerializer serializer)
        {
            Type type = typeof(MethodName);
            writer.WriteStartObject();
            foreach (KeyValuePair<MethodName, T> keyValue in (Dictionary<MethodName, T>)value)
            {
                writer.WritePropertyName(EnumUtil.GetEnumMemberValue(type, keyValue.Key));

                if (typeof(T).IsClass)
                {
                    JToken t = JToken.FromObject(keyValue.Value);
                    JObject o = (JObject)t;
                    IList<string> propertyNames = o.Properties().Select(p => p.Name).ToList();
                    o.AddFirst(new JProperty("Keys", new JArray(propertyNames)));
                    o.WriteTo(writer);
                }
                else
                {
                    writer.WriteValue(keyValue.Value);
                }
            }
            writer.WriteEndObject();
        }
    }
}
