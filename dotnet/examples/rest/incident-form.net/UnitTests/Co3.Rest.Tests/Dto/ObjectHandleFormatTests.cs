
using System;
using System.Runtime.Serialization;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Co3.Rest.Dto
{
    [TestClass]
    public class ObjectHandleFormatTests
    {
        /// <summary>
        /// Test to verify the ObjectHandleFormat's JSON values are what we expect.
        /// </summary>
        [TestMethod]
        public void TestObjectHandleFormatJsonNames()
        {
            Type type = typeof(ObjectHandleFormat);

            Array.ForEach((ObjectHandleFormat[])Enum.GetValues(type), handleFormat =>
            {
                if (handleFormat == ObjectHandleFormat.Undefined)
                    return;

                string name = Enum.GetName(type, handleFormat);
                EnumMemberAttribute attrib = ((EnumMemberAttribute[])type.GetField(name)
                    .GetCustomAttributes(typeof(EnumMemberAttribute), true))[0];

                switch (handleFormat)
                {
                    case ObjectHandleFormat.Default:
                        Assert.AreEqual("default", attrib.Value);
                        break;
                    case ObjectHandleFormat.Ids:
                        Assert.AreEqual("ids", attrib.Value);
                        break;
                    case ObjectHandleFormat.Names:
                        Assert.AreEqual("names", attrib.Value);
                        break;
                    case ObjectHandleFormat.Objects:
                        Assert.AreEqual("objects", attrib.Value);
                        break;
                    default:
                        Assert.Fail("Unhandled ObjectHandleFormat: " + attrib.Value);
                        break;
                }
            });
        }
    }
}
