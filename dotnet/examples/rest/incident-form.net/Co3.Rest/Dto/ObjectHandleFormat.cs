/*
 * Resilient Systems, Inc. ("Resilient") is willing to license software
 * or access to software to the company or entity that will be using or
 * accessing the software and documentation and that you represent as
 * an employee or authorized agent ("you" or "your") only on the condition
 * that you accept all of the terms of this license agreement.
 *
 * The software and documentation within Resilient's Development Kit are
 * copyrighted by and contain confidential information of Resilient. By
 * accessing and/or using this software and documentation, you agree that
 * while you may make derivative works of them, you:
 *
 * 1)  will not use the software and documentation or any derivative
 *     works for anything but your internal business purposes in
 *     conjunction your licensed used of Resilient's software, nor
 * 2)  provide or disclose the software and documentation or any
 *     derivative works to any third party.
 *
 * THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL RESILIENT BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

using System.Runtime.Serialization;
using Newtonsoft.Json;
using Newtonsoft.Json.Converters;

namespace Co3.Rest
{
    [JsonConverter(typeof(StringEnumConverter))]
    public enum ObjectHandleFormat
    {
        /// <summary>
        /// In this mode, the server is liberal in what it accepts for ObjectHandle values that are
        /// sent from the client.  If the client sends a string, then the server will perform a by-name
        /// lookup of that value.  If the the client sends an integer, then the server will perform
        /// a by-id lookup of that value.
        ///
        /// <para>The server will send ObjectHandle values back to the client as integer IDs.</para>
        ///
        /// <para>This is the default setting.</para>
        /// </summary>
        [EnumMember(Value = "default")]
        Default,

        /// <summary>
        /// In this mode, the server expects all ObjectHandle values that are sent from the client
        /// to be integer IDs.  If the client sends a string, we attempt to convert it to an integer.  If
        /// the string is not an integer (cannot be converted) then an error is returned.
        ///
        /// <para>The server sends ObjectHandle values back to the client as integer IDs.</para>
        ///
        /// <para>This is the behavior in v22 and before.</para>
        /// </summary>
        [EnumMember(Value = "ids")]
        Ids,

        /// <summary>
        /// In this mode, the server is liberal in what it accepts for ObjectHandle values that are
        /// sent from the client.  If the client sends a string, then the server will perform a by-name
        /// lookup of that value.  If the the client sends an integer, then the server will perform
        /// a by-id lookup of that value.
        ///
        /// <para>So far, this is the same as the "default" option.  The difference comes in how ObjectHandle
        /// values are sent back to the client.  If handle_format = names is specified then the object's
        /// name (string) will be sent back to the client).</para>
        /// </summary>
        [EnumMember(Value = "names")]
        Names,

        /// <summary>
        /// In this mode, the server will send all ObjectHandle values back to the client as objects
        /// </summary>
        [EnumMember(Value = "objects")]
        Objects
    }
}
