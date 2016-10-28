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

using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace Co3.Rest.Dto
{
    /// <summary>
    ///  Holds information about message destinations.  Message destinations are associated with actions so that when an action is triggered, a message is sent to the destination.
    /// </summary>
    public class MessageDestinationDto
    {

        /// <summary>
        ///  The ID of the destination.
        /// </summary>
        [JsonProperty("id")]
        public int Id { get; set; }

        /// <summary>
        ///  The visible name of the destination.
        /// </summary>
        [JsonProperty("name")]
        public string Name { get; set; }

        /// <summary>
        ///  The programmatic name of the destination.  This is how consumers will identify the message destination when accessing the message broker.
        /// </summary>
        [JsonProperty("programmatic_name")]
        public string ProgrammaticName { get; set; }

        /// <summary>
        ///  The type of the destination (e.g. queue or topic).  See constDTO message_destination_types property.
        /// </summary>
        [JsonProperty("destination_type")]
        public int DestinationType { get; set; }

        /// <summary>
        ///  Indicates whether an acknowledgement is expected for this destination.  If true, then the consumer of the messages sent to this queue must send a message to the "acks. ." queue.
        /// </summary>
        [JsonProperty("expect_ack")]
        public bool ExpectAck { get; set; }

        /// <summary>
        ///  The list of users which are permitted to receive messages in this message destination. Currently these users are only given read only access to the destination and write access to the ack queue (if it exists).
        /// </summary>
        [JsonProperty("users")]
        public List<ObjectHandle> Users { get; set; }

        /// <summary>
        ///  A unique identifier for this Message Destination.
        /// </summary>
        [JsonProperty("uuid")]
        public string Uuid { get; set; }

        /// <summary>
        ///  This value is used for export/import to uniquely represent this field
        /// </summary>
        [JsonProperty("export_key")]
        public string ExportKey { get; set; }

    }
}
