
using System;
using System.Runtime.Serialization;

namespace Co3.Rest.Util
{
    public static class EnumUtil
    {
        /// <summary>
        /// Returns the EnumMemberAttribute value of the specified enum value
        /// </summary>
        /// <param name="type">The enum's type</param>
        /// <param name="enumMember">The enum value</param>
        /// <returns>The JSON value of the enum</returns>
        public static string GetEnumMemberValue(Type type, object enumMember)
        {
            string name = Enum.GetName(type, enumMember);

            EnumMemberAttribute[] attribs = (EnumMemberAttribute[])type.GetField(name)
                .GetCustomAttributes(typeof(EnumMemberAttribute), true);
            if (attribs == null || attribs.Length == 0)
                return null;

            EnumMemberAttribute attrib = attribs[0];

            if (attrib == null)
                return null;

            return attrib.Value;
        }

        /// <summary>
        /// Translates the JSON string representation of the enum to the corresponding enum value
        /// </summary>
        /// <param name="type">The enum's type</param>
        /// <param name="value">The JSON string representing th enum</param>
        /// <returns>The num value, null if no match</returns>
        public static object GetEnumFromJsonName(Type type, string value)
        {
            string[] names = type.GetEnumNames();

            Array values = Enum.GetValues(type);
            for (int i = 0; i < values.Length; ++i)
            {
                string name = Enum.GetName(type, values.GetValue(i));
                EnumMemberAttribute[] attribs = (EnumMemberAttribute[])type.GetField(name)
                    .GetCustomAttributes(typeof(EnumMemberAttribute), true);

                if (attribs == null || attribs.Length == 0)
                    continue;

                EnumMemberAttribute attrib = attribs[0];

                if (attrib != null && string.Compare(attrib.Value, value, true) == 0)
                    return values.GetValue(i);
            }

            return null;
        }
    }
}
