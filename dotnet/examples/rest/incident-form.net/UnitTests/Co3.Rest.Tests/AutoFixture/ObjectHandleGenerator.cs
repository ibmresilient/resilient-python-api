using System;
using Co3.Rest.Dto;
using Ploeh.AutoFixture.Kernel;

namespace Co3.Rest.AutoFixture
{
    public class ObjectHandleGenerator : ISpecimenBuilder
    {
        static readonly Type s_type = typeof(ObjectHandle);

        public object Create(object request, ISpecimenContext context)
        {
            Type type = request as Type;

            if (type == null || type != s_type)
                return new NoSpecimen();

            return new ObjectHandle
            {
                Id = Generator.Generate<int>(),
                Name = Generator.Generate<string>()
            };
        }
    }
}
