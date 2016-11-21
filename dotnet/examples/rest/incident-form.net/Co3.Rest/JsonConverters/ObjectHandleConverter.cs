using System;
using System.Collections.Generic;
using System.Diagnostics.Eventing.Reader;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Co3.Rest.Dto;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Co3.Rest.JsonConverters
{
    public class ObjectHandleConverter : JsonConverter
    {
        private readonly HandleFormat m_handleFormat;

        public ObjectHandleConverter()
            : this(HandleFormat.Objects)
        {

        }

        public ObjectHandleConverter(HandleFormat handleFormat)
        {
            m_handleFormat = handleFormat;
        }

        public override void WriteJson(JsonWriter writer, object value, JsonSerializer serializer)
        {
            if (value == null)
            {
                writer.WriteNull();
                return;
            }

            var objectHandle = (ObjectHandle)value;
            switch (m_handleFormat)
            {
                case HandleFormat.Ids:
                    writer.WriteValue(objectHandle.Id);
                    break;
                case HandleFormat.Names:
                    writer.WriteValue(objectHandle.Name);
                    break;
                case HandleFormat.Objects:
                    writer.WriteStartObject();
                    writer.WritePropertyName("id");
                    writer.WriteValue(objectHandle.Id);
                    writer.WritePropertyName("name");
                    writer.WriteValue(objectHandle.Name);
                    writer.WriteEndObject();
                    break;
            }
        }

        public override object ReadJson(JsonReader reader, Type objectType, object existingValue, JsonSerializer serializer)
        {
            if (reader.TokenType == JsonToken.Null)
                return null;

            var objectHandle = new ObjectHandle();
            switch (m_handleFormat)
            {
                case HandleFormat.Ids:
                    objectHandle.Id = serializer.Deserialize<int>(reader);
                    break;
                case HandleFormat.Names:
                    objectHandle.Name = serializer.Deserialize<string>(reader);
                    break;
                case HandleFormat.Objects:
                    serializer.Populate(reader, objectHandle);
                    break;
            }
            return objectHandle;
        }

        public override bool CanConvert(Type objectType)
        {
            return (objectType == typeof(ObjectHandle));
        }
    }
}
