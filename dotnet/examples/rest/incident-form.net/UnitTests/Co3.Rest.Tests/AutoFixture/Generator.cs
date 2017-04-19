using System;
using Ploeh.AutoFixture;
using Ploeh.AutoFixture.Kernel;

namespace Co3.Rest.AutoFixture
{
    public static class Generator
    {
        static Fixture s_fixture;

        static Generator()
        {
            s_fixture = new Fixture();
            s_fixture.Behaviors.Add(new OmitOnRecursionBehavior(1));
            s_fixture.Customizations.Add(new IPAddressGenerator());
            s_fixture.Customizations.Add(new ObjectHandleGenerator());
            s_fixture.Customizations.Add(new EnumGenerator());
        }

        public static T Generate<T>()
        {
            return s_fixture.Create<T>();
        }

        public static object Generate(Type type)
        {
            return new SpecimenContext(s_fixture).Resolve(type);
        }
    }
}
