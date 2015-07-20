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

package com.co3.examples;

import java.util.List;

import com.fasterxml.jackson.core.type.TypeReference;
import org.junit.Test;
import org.mockito.ArgumentCaptor;

import com.co3.dto.json.GroupDTO;
import com.co3.dto.json.InvitationDetailsDTO;
import com.co3.dto.json.PermsDTO;
import com.co3.examples.InviteUsers.InviteUsersOptions;
import com.co3.simpleclient.SimpleClient;
import com.google.common.collect.Lists;

import static org.junit.Assert.*;
import static org.mockito.Mockito.*;

public class InviteUsersTest {

    @SuppressWarnings("unchecked")
    @Test
    public void testInvite() {
        InviteUsersOptions options = new InviteUsersOptions();
      
        String[] args = {
                "-url",
                "http://tester",
                "-email",
                "fred@xyz.com",
                "-password",
                "xyz", 
                "-group",
                "group1",
                "-group",
                "group2",
                "-noinc",
                "-observer",
                "user1@xyz.com",
                "user2@xyz.com",
                "user3@xyz.com"
        };
        
        options.parse(args);
       
        final SimpleClient mockClient = mock(SimpleClient.class);
        
        InviteUsers inviteUsers = new InviteUsers(options) {
            @Override
            protected SimpleClient newSimpleClient() {
                return mockClient;
            }
        };
       
        String orgUrl = "/rest/invitations/54321";
        String invitesUrl = String.format("%s/invitations", orgUrl);
        String groupsUrl = String.format("%s/groups", orgUrl);
        
        when(mockClient.getOrgURL("/invitations")).thenReturn(invitesUrl);
        when(mockClient.getOrgURL("/groups")).thenReturn(groupsUrl);
       
        // Capture all InvitationDetailsDTO objects that are posted.  Note that we
        // just return null here since we know that InviteUsers doesn't (currently)
        // use the returned values.
        //
        ArgumentCaptor<InvitationDetailsDTO> captor = ArgumentCaptor.forClass(InvitationDetailsDTO.class);
        
        when(mockClient.post(eq(invitesUrl), captor.capture(), any(TypeReference.class))).thenReturn(null);
        
        // InviteUsers will query for the list of groups to translate from name to ID.
        //
        GroupDTO group1 = new GroupDTO();
        group1.setId(5);
        group1.setName("group1");
        
        GroupDTO group2 = new GroupDTO();
        group2.setId(55);
        group2.setName("group2");
        
        List<GroupDTO> groups = Lists.newArrayList(group1, group2);
       
        when(mockClient.get(eq(groupsUrl), any(TypeReference.class))).thenReturn(groups);
        
        inviteUsers.run();
        
        // Make sure we captured objects for all users.
        //
        List<InvitationDetailsDTO> captured = captor.getAllValues();
        
        assertEquals(3, captured.size());
        
        for (InvitationDetailsDTO invite : captured) {
            PermsDTO perms = invite.getRoles();
            
            assertFalse(perms.getMasterAdministrator());
            assertFalse(perms.getAdministrator());
            assertTrue(perms.getObserver());
            assertFalse(perms.getCreateIncs());
            
            assertTrue(invite.getGroupIds().contains(group1.getId()));
            assertTrue(invite.getGroupIds().contains(group2.getId()));
        }
        
        assertEquals("user1@xyz.com", captured.get(0).getEmail());
        assertEquals("user2@xyz.com", captured.get(1).getEmail());
        assertEquals("user3@xyz.com", captured.get(2).getEmail());
    }
}
