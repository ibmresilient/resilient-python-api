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
    ///  Holds "permissions" applicable to a method name/operation, such as whether it should appear in conditions for manual actions, automatic actions and notifications.
    /// </summary>
    public class MethodNamePermsDto
    {

        /// <summary>
        ///  Should this method appear in picklists for manual actions?  For example, methods that require "previous values" such as "changed_to" cannot be used in manual actions because there is no concept of a previous value when the list of visible manual actions are calculated.
        /// </summary>
        [JsonProperty("show_in_manual_actions")]
        public bool ShowInManualActions { get; set; }

        /// <summary>
        ///  Should this method appear in picklists for automatic actions?
        /// </summary>
        [JsonProperty("show_in_auto_actions")]
        public bool ShowInAutoActions { get; set; }

        [Obsolete]
        public bool ShowInAutomaticActions
        {
            get { return ShowInAutoActions; }
            set { ShowInAutoActions = value; }
        }

        /// <summary>
        ///  Should this method appear in picklists for automatic notifications?
        /// </summary>
        [JsonProperty("show_in_notifications")]
        public bool ShowInNotifications { get; set; }

    }
}
