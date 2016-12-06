using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows.Markup;
using Co3.Rest.Dto;
using Newtonsoft.Json;

namespace Co3.Rest.JsonConverters
{
    public class ObjectHandleKeyConverter<T> : JsonConverter
    {
        public override void WriteJson(JsonWriter writer, object value, JsonSerializer serializer)
        {
            var values = (Dictionary<ObjectHandle, T>)value;
            var isIdsHandleFormat = values.Keys.All(k => string.IsNullOrEmpty(k.Name));

            writer.WriteStartObject();
            foreach (var keyValue in values)
            {
                writer.WritePropertyName(isIdsHandleFormat ? keyValue.Key.Id.ToString() : keyValue.Key.Name);
                writer.WriteValue(keyValue.Value);
            }
            writer.WriteEndObject();
        }

        public override object ReadJson(JsonReader reader, Type objectType, object existingValue, JsonSerializer serializer)
        {
            var returnValues = new Dictionary<ObjectHandle, T>();
            foreach (var value in serializer.Deserialize<Dictionary<string, T>>(reader))
            {
                var objectHandle = new ObjectHandle();
                var key = value.Key;
                int id;
                if (int.TryParse(key, out id))
                {
                    objectHandle.Id = id;
                }
                else
                {
                    objectHandle.Name = key;
                }
                returnValues.Add(objectHandle, value.Value);
            }
            return returnValues;
        }

        public override bool CanConvert(Type objectType)
        {
            return objectType.IsAssignableFrom(typeof(Dictionary<ObjectHandle, T>));
        }
    }
}