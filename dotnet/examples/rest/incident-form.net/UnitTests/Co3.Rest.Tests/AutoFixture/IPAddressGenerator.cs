using System;
using System.Net;
using Ploeh.AutoFixture.Kernel;

namespace Co3.Rest.AutoFixture
{
    public class IPAddressGenerator : ISpecimenBuilder
    {
        static readonly Type s_type = typeof(IPAddress);

        public object Create(object request, ISpecimenContext context)
        {
            Type type = request as Type;
            if (type == null || type != typeof(IPAddress))
                return new NoSpecimen();

            return new IPAddress(new byte[]
                {
                    Generator.Generate<byte>(),
                    Generator.Generate<byte>(),
                    Generator.Generate<byte>(),
                    Generator.Generate<byte>()
                });
        }
    }
}
