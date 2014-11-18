/*
 * Co3 Systems, Inc. ("Co3") is willing to license software or access to 
 * software to the company or entity that will be using or accessing the 
 * software and documentation and that you represent as an employee or 
 * authorized agent ("you" or "your" only on the condition that you 
 * accept all of the terms of this license agreement.
 *
 * The software and documentation within Co3's Development Kit are 
 * copyrighted by and contain confidential information of Co3. By 
 * accessing and/or using this software and documentation, you agree 
 * that while you may make derivative works of them, you:
 * 
 * 1)   will not use the software and documentation or any derivative 
 *      works for anything but your internal business purposes in 
 *      conjunction your licensed used of Co3's software, nor
 * 2)   provide or disclose the software and documentation or any 
 *      derivative works to any third party.
 * 
 * THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS 
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
 * ARE DISCLAIMED. IN NO EVENT SHALL CO3 BE LIABLE FOR ANY DIRECT, 
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, 
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED 
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package com.co3.examples;

import java.util.List;

import org.apache.commons.cli.Options;
import org.codehaus.jackson.type.TypeReference;

import com.co3.dto.json.GroupDTO;
import com.co3.dto.json.InvitationDetailsDTO;
import com.co3.dto.json.PermsDTO;
import com.co3.simpleclient.SimpleClient;
import com.google.common.collect.Lists;

/**
 * Command line application to invite users.
 */
public class InviteUsers {
    /**
     * Cache of group objects.
     */
    private List<GroupDTO> allGroups = null;
   
    /**
     * The options for this tool.  Co3Options handles common options such as -email, -password, -url, etc.
     */
    static class InviteUsersOptions extends Co3Options {
        private static final String GROUP_ARG = "group";
        private static final String REGULAR_ADMIN_ARG = "admin";
        private static final String OBSERVER_ARG = "observer";
        private static final String NO_CREATE_INCS_ARG = "noinc";
        
        public InviteUsersOptions() {
            super("[options] [emailaddr1] [emailaddr2] ...");
        }

        @Override
        protected void addOptions(Options options) {
            options.addOption(GROUP_ARG, true, "Group the user will be a member of");
            options.addOption(REGULAR_ADMIN_ARG, false, "The user will be an administrator");
            options.addOption(OBSERVER_ARG, false, "The user will be an observer");
            options.addOption(NO_CREATE_INCS_ARG, false, "The user CANNOT create incidents");
        }
       
        /**
         * @return The list of groups specified on the command line or in the config file.
         */
        List<String> getGroups() {
            return getConfigList(GROUP_ARG);
        }
       
        /**
         * @return true if -admin was specified, false otherwise.
         */
        boolean isAdmin() {
            return hasConfigValue(REGULAR_ADMIN_ARG);
        }
        
        /**
         * @return true if -observer was specified, false otherwise.
         */
        boolean isObserver() {
            return hasConfigValue(OBSERVER_ARG);
        }
        
        /**
         * @return true if -noinc was specified, false otherwise.  Note that
         * the absense of -noinc means that the user CAN create incidents.
         */
        boolean isNoCreateIncs() {
            return hasConfigValue(NO_CREATE_INCS_ARG);
        }
    }

    private InviteUsersOptions options;

    /**
     * Creates a new InviteUsers object with the specified options.
     * @param options The options to use.
     */
    InviteUsers(InviteUsersOptions options) {
        this.options = options;
    }

    /**
     * Finds a group ID given it's name.
     * @param client The client object to use to connect.
     * @param groupName The group name.
     * @return The group ID.
     * @throws IllegalArgumentException if the group does not exist on the server.
     */
    private int findGroupId(SimpleClient client, String groupName) {
        if (allGroups == null) {
            String url = client.getOrgURL("/groups");
            
            allGroups = client.get(url, new TypeReference<List<GroupDTO>>(){});
        }
        
        for (GroupDTO group : allGroups) {
            if (group.getName().equalsIgnoreCase(groupName)) {
                return group.getId();
            }
        }
        
        throw new IllegalArgumentException(String.format("Unable to locate group:  %s", groupName));
    }
   
    /**
     * Reads the options and creates the user invites.
     */
    void run() {
        try {
            // Create a SimpleClient object.
            //
            SimpleClient client = newSimpleClient();
   
            // Get the URL (it'll look like this:  /rest/orgs/{orgId}/invitations
            //
            String url = client.getOrgURL("/invitations");
           
            // For each email argument, post the invitation.
            //
            for (String email : options.getArgs()) {
                InvitationDetailsDTO details = new InvitationDetailsDTO();
               
                details.setEmail(email);
              
                // Convert group names to group IDs.  The heavy lifting is
                // in findGroupId.
                //
                List<Integer> groupIds = Lists.newArrayList();
               
                for (String groupName : options.getGroups()) {
                    groupIds.add(findGroupId(client, groupName));
                }
                
                details.setGroupIds(groupIds);
              
                // Indicate the pending user's permissions.
                //
                PermsDTO perms = new PermsDTO();
                
                perms.setAdministrator(options.isAdmin());
                perms.setObserver(options.isObserver());
                perms.setCreateIncs(!options.isNoCreateIncs());
                perms.setMasterAdministrator(false);
                
                details.setRoles(perms);
               
                // Create the invitation.
                //
                client.post(url, details, new TypeReference<InvitationDetailsDTO>(){});
                
                System.out.printf("Created invitation for %s\n", email);
            }
        } catch (Exception e) {
        	e.printStackTrace();
        }
    }
   
    /**
     * Creates a new SimpleClient object given our config options.  Note that
     * this is used for unit testing (overridden in unit tests to provide a mock).
     * @return A SimpleClient that can be used to interact with the server.
     */
    protected SimpleClient newSimpleClient() {
        // Create a SimpleClient object.
        //
        Co3Options.PasswordInfo info = options.getPasswordInfo();
    
        SimpleClient client = new SimpleClient(options.getBaseURL(),
                options.getOrgName(), info.getEmail(), info.getPassword());
   
        return client;
    }
    
    /**
     * Main entry point.
     * @param args The command line arguments.
     */
    public static void main(String[] args) {
        InviteUsersOptions options = new InviteUsersOptions();

        options.parse(args);

        new InviteUsers(options).run();
    }

}
