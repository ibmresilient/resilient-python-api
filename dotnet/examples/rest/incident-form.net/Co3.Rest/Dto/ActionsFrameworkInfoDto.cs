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
    ///  Holds information about the actions framework.
    /// </summary>
    public class ActionsFrameworkInfoDto
    {

        /// <summary>
        ///  Is the actions framework enabled and licensed?
        /// </summary>
        [JsonProperty("enabled")]
        public bool Enabled { get; set; }

        /// <summary>
        ///  A list of possible message destination types. The following are examples: Queue Topic
        /// The key portion of the map is the message destination type id, the value contains the visible name.
        /// </summary>
        [JsonProperty("destination_types")]
        public Dictionary<int, string> DestinationTypes { get; set; }

        /// <summary>
        ///  A list of possible action types. The following are examples: Automatic Manual
        /// The key portion of the map is the action type id, the value contains the visible name.
        /// </summary>
        [JsonProperty("action_types")]
        public Dictionary<int, string> ActionTypes { get; set; }

        /// <summary>
        ///  A list of possible action object types. The following are examples: Incident Task Note Milestone Artifact
        /// The key portion of the map is the action object type id, the value contains the visible name.
        /// </summary>
        [JsonProperty("action_object_types")]
        public Dictionary<int, string> ActionObjectTypes { get; set; }

        /// <summary>
        ///  A list of possible action invocation statuses. The following are examples: Complete Pending Error Timed Out
        /// The key portion of the map is the action invocation status id, the value contains the visible name.
        /// </summary>
        [JsonProperty("action_invocation_statuses")]
        public Dictionary<int, string> ActionInvocationStatuses { get; set; }

        /// <summary>
        ///  A list of possible action invocation message types. The following are examples: Information Error Warning
        /// The key portion of the map is the action invocation message type id, the value contains the visible name.
        /// </summary>
        [JsonProperty("action_invocation_message_types")]
        public Dictionary<int, string> ActionInvocationMessageTypes { get; set; }
    }
}
