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
    ///  Represents a notification in the system.  In the Co3 UI, these can be seen under the "globe" icon.
    /// </summary>
    public class NotificationDto
    {

        /// <summary>
        ///  The user ID of the person who is to receive the notification.  The fullOrgDTO (users property)contains a list of all the possible user values.
        /// </summary>
        [JsonProperty("recipient_muser_id")]
        public int RecipientMuserId { get; set; }

        /// <summary>
        ///  The notification ID.
        /// </summary>
        [JsonProperty("id")]
        public int Id { get; set; }

        /// <summary>
        ///  The date the notification was created.
        /// </summary>
        [JsonProperty("create_date")]
        public DateTime CreateDate { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("email_date")]
        public DateTime EmailDate { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("ack_date")]
        public DateTime AckDate { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("notification_def")]
        public NotificationDefDto NotificationDef { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("inc_id")]
        public int IncId { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("inc_training")]
        public bool IncTraining { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("inc_name")]
        public string IncName { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("task_name")]
        public string TaskName { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("task_id")]
        public int TaskId { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("comment_text")]
        public string CommentText { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("comment_id")]
        public int CommentId { get; set; }

        /// <summary>
        ///  The user ID of the person who originated the notification.  The fullOrgDTO (users property)contains a list of all the possible user values.
        /// </summary>
        [JsonProperty("originating_muser_id")]
        public int OriginatingMuserId { get; set; }

        /// <summary>
        ///  The user name of the person who originated the notification.
        /// </summary>
        [JsonProperty("originating_muser_name")]
        public string OriginatingMuserName { get; set; }

    }
}
