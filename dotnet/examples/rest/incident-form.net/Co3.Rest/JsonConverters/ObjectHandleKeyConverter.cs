using System;
using System.Collections.Generic;
using Co3.Rest.Dto;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Co3.Rest.JsonConverters
{
    public class ObjectHandleKeyConverter : JsonConverter
    {
        public override void WriteJson(JsonWriter writer, object value, JsonSerializer serializer)
        {
            throw new NotImplementedException();
        }

        public override object ReadJson(JsonReader reader, Type objectType, object existingValue, JsonSerializer serializer)
        {
            var returnValues = new Dictionary<ObjectHandle, bool>();
            foreach (var value in serializer.Deserialize<Dictionary<string, bool>>(reader))
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
            return objectType.IsAssignableFrom(typeof(Dictionary<ObjectHandle, bool>));
        }

        public override bool CanWrite
        {
            get { return false; }
        }
    }
}