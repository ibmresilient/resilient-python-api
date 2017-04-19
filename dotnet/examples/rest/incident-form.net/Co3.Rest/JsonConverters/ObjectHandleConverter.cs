using System;
using Co3.Rest.Dto;
using Newtonsoft.Json;

namespace Co3.Rest.JsonConverters
{
    public class ObjectHandleConverter : JsonConverter
    {
        private readonly ObjectHandleFormat m_handleFormat;

        public ObjectHandleConverter()
            : this(ObjectHandleFormat.Objects)
        {

        }

        public ObjectHandleConverter(ObjectHandleFormat handleFormat)
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
                case ObjectHandleFormat.Ids:
                    writer.WriteValue(objectHandle.Id);
                    break;
                case ObjectHandleFormat.Names:
                    writer.WriteValue(objectHandle.Name);
                    break;
                case ObjectHandleFormat.Objects:
                case ObjectHandleFormat.Default:
                    writer.WriteStartObject();
                    writer.WritePropertyName("id");
                    writer.WriteValue(objectHandle.Id);
                    writer.WritePropertyName("name");
                    writer.WriteValue(objectHandle.Name);
                    writer.WriteEndObject();
                    break;
                default:
                    throw new NotImplementedException(string.Format("{0} is not supported.", m_handleFormat));
            }
        }

        public override object ReadJson(JsonReader reader, Type objectType, object existingValue, JsonSerializer serializer)
        {
            if (reader.TokenType == JsonToken.Null)
                return null;

            var objectHandle = new ObjectHandle();
            switch (m_handleFormat)
            {
                case ObjectHandleFormat.Ids:
                    objectHandle.Id = serializer.Deserialize<int>(reader);
                    break;
                case ObjectHandleFormat.Names:
                    objectHandle.Name = serializer.Deserialize<string>(reader);
                    break;
                case ObjectHandleFormat.Objects:
                    serializer.Populate(reader, objectHandle);
                    break;
                default:
                    switch (reader.TokenType)
                    {
                        case JsonToken.StartObject:
                            serializer.Populate(reader, objectHandle);
                            break;
                        case JsonToken.String:
                            objectHandle.Name = serializer.Deserialize<string>(reader);
                            break;
                        case JsonToken.Integer:
                            objectHandle.Id = serializer.Deserialize<int>(reader);
                            break;
                        default:
                            throw new NotImplementedException(reader.TokenType.ToString());
                    }
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
